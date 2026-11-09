"""Complexity feature — round 2: prompt-technique A/B across the top model classes.

Round 1 narrowed the catalog to a top tier; round 2 asks the *other* question:
for the three strongest and architecturally-distinct models, does a better
PROMPT lift format-validity (and accuracy) — and does the lift generalize across
model classes? Round 1 showed the winner's failures were almost all
`assumptions`-as-array and markdown fences, i.e. an output-contract mismatch, not
bad analysis. So we test named prompting techniques from the course lectures.

Everything except the system-prompt text (and, for V5, the parser) is identical
to the real pipeline: the guards spotlighting+canary wrapper, the ComplexityResult
schema, the same 7 known-answer fixtures. The independent variable is the prompt.

Variants (named techniques):
  V0 zero-shot-baseline   current COMPLEXITY_PROMPT, unchanged (control)
  V1 zero-shot-format     baseline + explicit format constraints (string assumptions, raw JSON, no fences)
  V2 few-shot             V1 + one worked code->JSON example
  V3 chain-of-thought     reason step-by-step, then emit JSON last (strict parse: measures CoT-vs-strict-JSON conflict)
  V4 role-persona         V1 framed as a static-analysis tool that emits only machine-readable JSON
  V5 lenient-parse        V1 wording, but parsed with the guards' first-{...} extractor instead of strict json.loads

Models: three different classes — ornith1.5:35b (ornith), x-test-2 (x-test),
qwen3.6:35b (qwen).

Run from backend/ (Python 3.14 venv):
    .venv/bin/python ../workflow/live-ai/complexity_prompt_round2.py
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
from app.ai.complexity import ComplexityResult  # noqa: E402
from app.clients.llm import LLMClient  # noqa: E402

from complexity_fixtures import CASES  # noqa: E402
from complexity_model_selection import COMPLEXITY_PROMPT, _load_env, _matches  # noqa: E402

MODELS = ["ornith1.5:35b", "x-test-2", "qwen3.6:35b"]
TRIALS = 3
_SEM = asyncio.Semaphore(8)

# --- format directives reused by V1/V2/V4/V5 -------------------------------
_FORMAT_RULES = (
    " Output requirements: return ONLY a single raw JSON object and nothing else "
    "— no markdown, no ``` code fences, no text before or after. The fields "
    "time_complexity, space_complexity, explanation, and assumptions must each be "
    "a single plain-text string (assumptions is ONE string, never a JSON array or "
    "list). Do not add any keys beyond those four."
)

# One worked example for the few-shot variant (V2). Uses a code snippet NOT in
# the fixture set so it demonstrates the shape without leaking a test answer.
_FEWSHOT_EXAMPLE = (
    '\n\nExample (for format only; analyze the real code below, not this):\n'
    "code:\n"
    "def peek(stack):\n"
    "    return stack[-1]\n"
    "output:\n"
    '{"time_complexity": "O(1)", "space_complexity": "O(1)", '
    '"explanation": "Single indexed access to the last element; no loops or '
    'recursion, so cost is constant and no auxiliary structures are allocated.", '
    '"assumptions": "stack is a non-empty sequence with O(1) indexing such as a '
    'Python list; an empty stack would raise IndexError."}'
)

_ROLE_PREAMBLE = (
    "You are a static code-analysis tool. You do not converse. You emit only "
    "machine-readable JSON that a program will parse. "
)


def _variant_prompt(variant: str) -> str:
    base = COMPLEXITY_PROMPT
    if variant == "V0 zero-shot-baseline":
        return base
    if variant == "V1 zero-shot-format":
        return base + _FORMAT_RULES
    if variant == "V2 few-shot":
        return base + _FORMAT_RULES + _FEWSHOT_EXAMPLE
    if variant == "V3 chain-of-thought":
        return (
            base
            + " First think step by step about the loops, recursion, and data "
            "structures and how they scale. Then, as the LAST thing in your reply, "
            "output the final answer as a single raw JSON object with exactly the "
            "fields time_complexity, space_complexity, explanation, assumptions "
            "(each a plain-text string)."
        )
    if variant == "V4 role-persona":
        return _ROLE_PREAMBLE + base + _FORMAT_RULES
    if variant == "V5 lenient-parse":
        return base + _FORMAT_RULES
    raise ValueError(variant)


VARIANTS = [
    "V0 zero-shot-baseline",
    "V1 zero-shot-format",
    "V2 few-shot",
    "V3 chain-of-thought",
    "V4 role-persona",
    "V5 lenient-parse",
]


def _parse_strict(content: str) -> ComplexityResult:
    return ComplexityResult.model_validate(json.loads(content))


def _parse_lenient(content: str, canary: str) -> ComplexityResult:
    # Mirrors guards.extract_json_object: find the first {...} and raw_decode it,
    # tolerating markdown fences / prose around the JSON.
    obj = guards.extract_json_object(content, canary)
    return ComplexityResult.model_validate(obj)


async def _one_call(client: LLMClient, prompt: str, variant: str, code: str) -> tuple[ComplexityResult | None, float, str]:
    nonce, canary = guards.new_nonce(), guards.new_canary()
    messages = [
        {"role": "system", "content": guards.build_system_prompt(prompt, nonce, canary)},
        {"role": "user", "content": guards.wrap_untrusted("submitted_code", code, nonce)},
    ]
    async with _SEM:
        start = time.monotonic()
        try:
            reply = await client.chat(messages, max_tokens=1500)
        except Exception as exc:  # noqa: BLE001
            return None, time.monotonic() - start, f"call_error:{type(exc).__name__}"
        latency = time.monotonic() - start
    try:
        guards.check_canary(reply.content, canary)
    except Exception:  # noqa: BLE001
        return None, latency, "canary_leak"
    if len(reply.content) > 5000 or reply.tool_calls:
        return None, latency, "too_long_or_tool_calls"
    try:
        if variant == "V5 lenient-parse":
            result = _parse_lenient(reply.content, canary)
        else:
            result = _parse_strict(reply.content)
    except Exception:  # noqa: BLE001
        return None, latency, "invalid_schema_or_json"
    return result, latency, "ok"


async def _probe_cell(base: str, key: str, model: str, variant: str) -> dict:
    client = LLMClient(base, key, model, chat_timeout_s=60.0)
    prompt = _variant_prompt(variant)
    jobs = [(case, _one_call(client, prompt, variant, case.code)) for case in CASES for _ in range(TRIALS)]
    try:
        outcomes = await asyncio.gather(*(coro for _, coro in jobs))
    finally:
        await client.aclose()
    valid = time_ok = space_ok = total = 0
    latencies: list[float] = []
    reasons: dict[str, int] = {}
    for (case, _), (result, latency, reason) in zip(jobs, outcomes):
        total += 1
        latencies.append(latency)
        reasons[reason] = reasons.get(reason, 0) + 1
        if result is None:
            continue
        valid += 1
        if _matches(result.time_complexity, case.time_accept):
            time_ok += 1
        if _matches(result.space_complexity, case.space_accept):
            space_ok += 1
    return {
        "model": model,
        "variant": variant,
        "total": total,
        "valid": valid,
        "time_ok": time_ok,
        "space_ok": space_ok,
        "median_latency": round(statistics.median(latencies), 2) if latencies else None,
        "reasons": reasons,
    }


def _render(results: list[dict]) -> str:
    lines = [
        "# Complexity feature — round 2: prompt-technique A/B",
        "",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S')}",
        "",
        f"Three model classes × {len(VARIANTS)} prompt variants × {len(CASES)} known-answer "
        f"fixtures × {TRIALS} trials ({len(CASES) * TRIALS} calls per cell). Identical guards "
        f"wrapper, canary, and ComplexityResult schema as the real pipeline; the system prompt "
        f"(and, for V5, the JSON parser) is the only variable. `valid` = passed canary + size + "
        f"schema. `time`/`space` = Big-O matched the known answer.",
        "",
        "## Format-valid rate (valid / 21) by model × variant",
        "",
        "| Variant | " + " | ".join(f"`{m}`" for m in MODELS) + " |",
        "| --- | " + " | ".join("---:" for _ in MODELS) + " |",
    ]
    by_key = {(r["model"], r["variant"]): r for r in results}
    for v in VARIANTS:
        cells = []
        for m in MODELS:
            r = by_key.get((m, v))
            cells.append(f"{r['valid']}/{r['total']}" if r else "—")
        lines.append(f"| {v} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Correct Big-O (time+space both correct, / 21) by model × variant")
    lines.append("")
    lines.append("| Variant | " + " | ".join(f"`{m}`" for m in MODELS) + " |")
    lines.append("| --- | " + " | ".join("---:" for _ in MODELS) + " |")
    for v in VARIANTS:
        cells = []
        for m in MODELS:
            r = by_key.get((m, v))
            if r:
                both = min(r["time_ok"], r["space_ok"])
                cells.append(f"{both}/{r['total']}")
            else:
                cells.append("—")
        lines.append(f"| {v} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Median latency (s) by model × variant")
    lines.append("")
    lines.append("| Variant | " + " | ".join(f"`{m}`" for m in MODELS) + " |")
    lines.append("| --- | " + " | ".join("---:" for _ in MODELS) + " |")
    for v in VARIANTS:
        cells = []
        for m in MODELS:
            r = by_key.get((m, v))
            cells.append(f"{r['median_latency']}" if r else "—")
        lines.append(f"| {v} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Failure reasons per cell")
    lines.append("")
    for v in VARIANTS:
        for m in MODELS:
            r = by_key.get((m, v))
            if not r:
                continue
            bad = {k: val for k, val in r["reasons"].items() if k != "ok"}
            if bad:
                lines.append(
                    f"- `{m}` / {v}: " + ", ".join(f"{k}×{val}" for k, val in sorted(bad.items()))
                )
    lines.append("")
    return "\n".join(lines)


async def main() -> int:
    _load_env()
    base, key = os.environ["SOCLAAS_BASE_URL"], os.environ["SOCLAAS_API_KEY"]
    out = HERE / "complexity-prompt-round2.md"
    print(f"{len(MODELS)} models × {len(VARIANTS)} variants × {len(CASES)}×{TRIALS} calls ...", file=sys.stderr)
    results: list[dict] = []
    for model in MODELS:
        for variant in VARIANTS:
            print(f"  {model} / {variant} ...", file=sys.stderr, flush=True)
            r = await _probe_cell(base, key, model, variant)
            results.append(r)
            both = min(r["time_ok"], r["space_ok"])
            print(
                f"    -> valid {r['valid']}/{r['total']}, bigO {both}/{r['total']}, "
                f"median {r['median_latency']}s",
                file=sys.stderr,
                flush=True,
            )
            out.write_text(_render(results) + "\n", encoding="utf-8")
    print(f"Wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
