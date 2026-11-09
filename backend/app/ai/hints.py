"""Student hint: a bounded tool loop (spec §7.1)."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from app.ai import guards
from app.config import AppContext
from app.jobs.runner import UserFacingError
from app.repos import questions as questions_repo

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3
REVIEW_EXPECTED_ERRORS = (UserFacingError, TimeoutError, ValueError)
REVIEW_TIMEOUT_S = 20.0
REVIEW_DEADLINE_MARGIN_S = 1.0
REVIEW_MAX_BYTES = 64 * 1024
REVIEW_PROMPT = """You are a private hint reviewer. Decide whether the candidate is a useful hint and whether it reveals the answer. A hint reveals the answer if it states a hidden expected output, gives a full or near-full solution, or provides working solution code. The tagged question context and candidate hint are JSON strings; the hidden expected outputs are a JSON array. Interpret JSON escapes to recover their exact text. Return only JSON with exactly two boolean fields: is_hint and reveals_answer. Never repeat protected data."""
MAX_TOKENS = 1024
_BASE_PROMPT = (Path(__file__).parent / "prompts" / "hint.md").read_text()

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": {}},
        },
    }
    for name, description in (
        ("get_question", "Get the question: title, statement, limits and the visible test cases."),
        ("get_code", "Get the student's current code."),
    )
]


async def run_hint(ctx: AppContext, job_input: dict[str, Any]) -> dict[str, Any]:
    question = await questions_repo.get(ctx.db, job_input["question_id"])
    if question is None:
        raise UserFacingError("The question no longer exists.")
    code: str = job_input["code"]
    visible = [t for t in question.test_cases if not t.is_hidden]

    def get_question() -> str:
        lines = [
            f"Title: {question.title}",
            f"Time limit: {question.time_limit_ms} ms, memory limit: {question.memory_limit_mb} MB",
            "",
            question.statement_md,
            "",
            "Visible test cases:",
        ]
        for i, t in enumerate(visible, 1):
            lines += [f"Test {i} input:", t.stdin, f"Test {i} expected output:", t.expected_stdout]
        return "\n".join(lines)

    handlers = {"get_question": get_question, "get_code": lambda: code}

    nonce = guards.new_nonce()
    canary = guards.new_canary()
    asked = job_input.get("question")
    asked_line = (
        f"Their question: {guards.wrap_untrusted('student_question', asked, nonce)} "
        if asked
        else ""
    )
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": guards.build_system_prompt(_BASE_PROMPT, nonce, canary)},
        {
            "role": "user",
            "content": f"The student is stuck on the question {guards.wrap_untrusted('title', question.title, nonce)} and asks for a hint. "
            f"{asked_line}Use the tools to read the question and/or their code if you need them.",
        },
    ]
    tools_used: list[str] = []

    reply = await ctx.llm.chat(
        messages,
        tools=TOOLS,
        tool_choice="auto",
        max_tokens=MAX_TOKENS,
        model=ctx.settings.hint_generator_model,
    )
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
        reply = await ctx.llm.chat(
            messages,
            tools=TOOLS,
            tool_choice=choice,
            max_tokens=MAX_TOKENS,
            model=ctx.settings.hint_generator_model,
        )

    hint = guards.check_hint_output(reply.content, canary)
    if not hint:
        raise UserFacingError("The AI response was empty. Try again.")
    await _review_hint(ctx, question, get_question(), hint, job_input.get("_deadline"))
    return {"hint_md": hint, "tools_used": tools_used}


def _strict_verdict(text: str) -> dict[str, bool]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    value = json.loads(text, object_pairs_hook=pairs)
    if (
        not isinstance(value, dict)
        or set(value) != {"is_hint", "reveals_answer"}
        or any(type(v) is not bool for v in value.values())
    ):
        raise ValueError("invalid verdict")
    return value


async def _review_hint(
    ctx: AppContext, question: Any, context: str, hint: str, deadline: float | None
) -> None:
    nonce, canary = guards.new_nonce(), guards.new_canary()

    def encode_data(value: Any) -> str:
        # JSON escapes preserve literal tag-like content while keeping delimiters intact.
        return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")

    outputs = encode_data([t.expected_stdout for t in question.test_cases if t.is_hidden])
    payload = "\n\n".join(
        (
            guards.wrap_untrusted("question_context", encode_data(context), nonce),
            guards.wrap_untrusted("hidden_expected_outputs", outputs, nonce),
            guards.wrap_untrusted("candidate_hint", encode_data(hint), nonce),
        )
    )
    if len(payload.encode("utf-8")) > REVIEW_MAX_BYTES:
        logger.warning("Hint review skipped: input too large")
        return
    remaining = (
        REVIEW_TIMEOUT_S
        if deadline is None
        else min(
            REVIEW_TIMEOUT_S,
            deadline - asyncio.get_running_loop().time() - REVIEW_DEADLINE_MARGIN_S,
        )
    )
    if remaining <= 0:
        logger.warning("Hint review skipped: insufficient time")
        return
    try:
        async with asyncio.timeout(remaining):
            reply = await ctx.llm.chat(
                [
                    {
                        "role": "system",
                        "content": guards.build_system_prompt(REVIEW_PROMPT, nonce, canary),
                    },
                    {"role": "user", "content": payload},
                ],
                model=ctx.settings.hint_reviewer_model,
                max_tokens=128,
            )
        if canary in reply.content or reply.tool_calls:
            raise ValueError("invalid reviewer response")
        verdict = _strict_verdict(reply.content)
    except REVIEW_EXPECTED_ERRORS:
        logger.warning("Hint review failed or returned an invalid verdict")
        return
    except Exception:
        logger.error("Hint review encountered an unexpected error")
        return
    if not verdict["is_hint"] or verdict["reveals_answer"]:
        raise UserFacingError("The AI response was rejected. Try again.")
