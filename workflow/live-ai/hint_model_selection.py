"""Hint feature — live model-selection probe.

Replicates CodeIt's REAL hint pipeline (the exact _BASE_PROMPT from
app.ai.prompts/hint.md, the two get_question/get_code tools, the bounded ≤3-round
tool loop with tool_choice flipping to "none" on the last round, and the
app.ai.guards spotlighting + canary + check_hint_output guards) across the live
SoCLaaS catalog, on known-scenario fixtures.

Hint output is free-text Markdown, so there is no schema oracle. The probe records
what we CAN measure mechanically per model, and dumps the raw hint so a human can
judge quality:

  produced        — a non-empty hint survived the guards (canary-clean, non-empty)
  code_lines      — total lines inside fenced code blocks (prompt rule: ≤5)
  over_code       — code_lines > 5 (violates the feature's own constraint)
  answer_leak     — the hidden test's expected output appeared verbatim (hard leak)
  solution_leak   — the fixture's full_solution appeared (gave away the answer)
  chars           — hint length (cap is 4000)
  canary_leak     — guards.check_hint_output raised (model echoed the secret marker)
  tools_used      — which of get_question/get_code the model called
  median latency

Run from backend/ (Python 3.14 venv):
    .venv/bin/python ../workflow/live-ai/hint_model_selection.py
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.ai import guards  # noqa: E402
from app.ai.hints import MAX_TOKENS, MAX_TOOL_ROUNDS, TOOLS, _BASE_PROMPT  # noqa: E402
from app.clients.llm import LLMClient  # noqa: E402
from app.jobs.runner import UserFacingError  # noqa: E402

from hint_fixtures import CASES, HintCase  # noqa: E402

TRIALS = 2  # smaller than complexity: outputs are read by a human
SKIP_MODELS = {"bge-m3", "whisper-large-v3", "qwen3-vl:32b"}
_SEM = asyncio.Semaphore(8)
_FENCE_RE = re.compile(r"(?P<fence>```|~~~)[^\n]*\n(?P<body>.*?)(?:(?P=fence)|\Z)", re.DOTALL)


def _code_line_count(text: str) -> int:
    total = 0
    for m in _FENCE_RE.finditer(text):
        body = m.group("body").rstrip("\n")
        if body:
            total += len(body.split("\n"))
    return total


def _build_handlers(case: HintCase):
    def get_question() -> str:
        lines = [
            f"Title: {case.title}",
            "Time limit: 1000 ms, memory limit: 256 MB",
            "",
            case.statement_md,
            "",
            "Visible test cases:",
        ]
        for i, t in enumerate(case.visible_tests, 1):
            lines += [f"Test {i} input:", t.stdin, f"Test {i} expected output:", t.expected_stdout]
        return "\n".join(lines)

    return {"get_question": get_question, "get_code": lambda: case.student_code}


async def _one_hint(client: LLMClient, case: HintCase) -> dict:
    """Run the real hint tool-loop once. Returns a record with raw output + facts."""
    handlers = _build_handlers(case)
    nonce, canary = guards.new_nonce(), guards.new_canary()
    asked = case.student_question
    asked_line = (
        f"Their question: {guards.wrap_untrusted('student_question', asked, nonce)} " if asked else ""
    )
    messages: list[dict] = [
        {"role": "system", "content": guards.build_system_prompt(_BASE_PROMPT, nonce, canary)},
        {
            "role": "user",
            "content": f"The student is stuck on the question {guards.wrap_untrusted('title', case.title, nonce)} and asks for a hint. "
            f"{asked_line}Use the tools to read the question and/or their code if you need them.",
        },
    ]
    tools_used: list[str] = []
    rec: dict = {"case": case.name}
    async with _SEM:
        start = time.monotonic()
        try:
            reply = await client.chat(messages, tools=TOOLS, tool_choice="auto", max_tokens=MAX_TOKENS)
            for round_no in range(1, MAX_TOOL_ROUNDS + 1):
                if not reply.tool_calls:
                    break
                messages.append(reply.assistant_message())
                for call in reply.tool_calls:
                    name = call.get("function", {}).get("name", "")
                    handler = handlers.get(name)
                    if handler is None:
                        content = "unknown tool"
                    else:
                        if name not in tools_used:
                            tools_used.append(name)
                        content = guards.wrap_untrusted(name, handler(), nonce)
                    messages.append(
                        {"role": "tool", "tool_call_id": call.get("id", ""), "content": content}
                    )
                choice = "none" if round_no == MAX_TOOL_ROUNDS else "auto"
                reply = await client.chat(messages, tools=TOOLS, tool_choice=choice, max_tokens=MAX_TOKENS)
        except Exception as exc:  # noqa: BLE001
            rec.update(latency=round(time.monotonic() - start, 2), error=f"{type(exc).__name__}", hint="")
            return rec
        latency = round(time.monotonic() - start, 2)

    raw = reply.content
    # Output guards exactly as production.
    try:
        hint = guards.check_hint_output(raw, canary)
        canary_leak = False
    except UserFacingError:
        hint, canary_leak = "", True

    rec.update(
        latency=latency,
        tools_used=list(tools_used),
        canary_leak=canary_leak,
        hint=hint,
        raw=raw,
        chars=len(hint),
        code_lines=_code_line_count(hint),
        answer_leak=_leaks_token(raw, case.leak_token),
        solution_leak=_normalize(case.full_solution) in _normalize(raw),
    )
    rec["over_code"] = rec["code_lines"] > 5
    rec["produced"] = bool(hint) and not canary_leak
    return rec


def _normalize(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _leaks_token(raw: str, token: str | None) -> bool:
    """A hidden-answer leak only counts for fixtures with a 'surprising' computed
    answer (leak_token set). Match on a word boundary so e.g. 350 does not match
    inside 3509, and skip categorical outputs (YES/NO/EMPTY) which are None."""
    if not token:
        return False
    return re.search(rf"(?<!\d){re.escape(token)}(?!\d)", raw) is not None


async def _probe_model(base: str, key: str, model: str) -> dict:
    client = LLMClient(base, key, model, chat_timeout_s=60.0)
    jobs = [_one_hint(client, c) for c in CASES for _ in range(TRIALS)]
    try:
        recs = await asyncio.gather(*jobs)
    finally:
        await client.aclose()
    lat = [r["latency"] for r in recs if "latency" in r]
    produced = sum(1 for r in recs if r.get("produced"))
    return {
        "model": model,
        "total": len(recs),
        "produced": produced,
        "over_code": sum(1 for r in recs if r.get("over_code")),
        "answer_leak": sum(1 for r in recs if r.get("answer_leak")),
        "solution_leak": sum(1 for r in recs if r.get("solution_leak")),
        "canary_leak": sum(1 for r in recs if r.get("canary_leak")),
        "errors": sum(1 for r in recs if r.get("error")),
        "median_latency": round(statistics.median(lat), 2) if lat else None,
        "records": recs,
    }


def _render_summary(results: list[dict]) -> str:
    results = sorted(results, key=lambda r: (-r["produced"], r["median_latency"] or 1e9))
    lines = [
        "# Hint feature — live model selection (deterministic signals)",
        "",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S')}",
        "",
        f"Real hint pipeline (prompt + get_question/get_code tool loop + guards) across the live "
        f"catalog, {len(CASES)} fixtures × {TRIALS} trials ({len(CASES) * TRIALS} runs per model). "
        f"Hint quality is judged by a human from `hint-model-selection-outputs.md`; this table is "
        f"only the mechanical signals. `produced` = non-empty, canary-clean hint. `over_code` = "
        f"more than 5 lines of fenced code (violates the feature rule). `answer_leak` = hidden "
        f"expected output appeared verbatim. `solution_leak` = the full reference solution appeared.",
        "",
        "| Model | produced | over_code | answer_leak | solution_leak | canary_leak | errors | median s |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in results:
        t = r["total"]
        lines.append(
            f"| `{r['model']}` | {r['produced']}/{t} | {r['over_code']} | {r['answer_leak']} | "
            f"{r['solution_leak']} | {r['canary_leak']} | {r['errors']} | {r['median_latency']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_outputs(results: list[dict]) -> str:
    lines = [
        "# Hint feature — raw model outputs for human judging",
        "",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S')}",
        "",
        "One block per (model, fixture, trial). Read these to judge hint QUALITY "
        "(helpful nudge? gives away the answer? on-topic? obeys ≤5 code lines?). The "
        "fixture's intended nudge and the hidden answer are shown first for reference.",
        "",
    ]
    from hint_fixtures import CASES as _C

    lines.append("## Fixtures (reference)")
    for c in _C:
        leak = f"`{c.leak_token}`" if c.leak_token else "(categorical output — not leak-scored)"
        lines.append(
            f"- **{c.name}** — defect: {c.defect}. good hint points at: {c.good_hint_points_at}. "
            f"must-not-reveal answer: {leak}"
        )
    lines.append("")
    for r in results:
        lines.append(f"## `{r['model']}`")
        lines.append("")
        for rec in r["records"]:
            if rec.get("error"):
                lines.append(f"### {rec['case']} — ERROR {rec['error']} ({rec.get('latency')}s)")
                lines.append("")
                continue
            flags = []
            if rec.get("over_code"):
                flags.append(f"OVER_CODE({rec['code_lines']})")
            if rec.get("answer_leak"):
                flags.append("ANSWER_LEAK")
            if rec.get("solution_leak"):
                flags.append("SOLUTION_LEAK")
            if rec.get("canary_leak"):
                flags.append("CANARY_LEAK")
            flagstr = (" [" + ", ".join(flags) + "]") if flags else ""
            tools = ",".join(rec.get("tools_used") or []) or "none"
            lines.append(
                f"### {rec['case']} ({rec.get('latency')}s, tools={tools}, "
                f"{rec.get('chars')} chars){flagstr}"
            )
            lines.append("")
            lines.append("```markdown")
            lines.append(rec.get("hint") or "(empty)")
            lines.append("```")
            lines.append("")
    return "\n".join(lines)


async def main() -> int:
    for line in (BACKEND / ".env").read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    base, key = os.environ["SOCLAAS_BASE_URL"], os.environ["SOCLAAS_API_KEY"]
    probe = LLMClient(base, key, "default", 30.0)
    try:
        catalog = await probe.list_models()
    finally:
        await probe.aclose()
    models = [m for m in catalog if m not in SKIP_MODELS]
    print(f"Testing {len(models)} models × {len(CASES)} fixtures × {TRIALS} trials ...", file=sys.stderr)
    summary_out = HERE / "hint-model-selection.md"
    outputs_out = HERE / "hint-model-selection-outputs.md"
    results = []
    for model in models:
        print(f"  {model} ...", file=sys.stderr, flush=True)
        r = await _probe_model(base, key, model)
        results.append(r)
        print(
            f"    -> produced {r['produced']}/{r['total']}, over_code {r['over_code']}, "
            f"answer_leak {r['answer_leak']}, solution_leak {r['solution_leak']}, "
            f"errors {r['errors']}, median {r['median_latency']}s",
            file=sys.stderr,
            flush=True,
        )
        summary_out.write_text(_render_summary(results) + "\n", encoding="utf-8")
        outputs_out.write_text(_render_outputs(results) + "\n", encoding="utf-8")
    print(f"Wrote {summary_out} and {outputs_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
