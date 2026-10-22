"""Teacher question generation job (spec §7.2)."""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.ai import guards
from app.config import AppContext
from app.jobs.runner import UserFacingError
from app.schemas import QuestionDraft, QuestionGenResult

INVALID_QUESTION = "The AI returned an invalid question. Try again."
MAX_TOKENS = 16384
_PROMPT = (Path(__file__).parent / "prompts" / "question_gen.md").read_text(encoding="utf-8")


def _user_message(job_input: dict[str, Any], nonce: str) -> str:
    wrap = lambda label, text: guards.wrap_untrusted(label, text, nonce)  # noqa: E731
    parts = [
        wrap("difficulty", job_input["difficulty"]),
        wrap("topics", ", ".join(job_input["topics"])),
        wrap("prompt", job_input["prompt"]),
    ]
    if job_input.get("parent_draft") is not None:
        parts.append(wrap("previous draft", json.dumps(job_input["parent_draft"])))
        parts.append(wrap("feedback", job_input["feedback"] or ""))
    return "\n\n".join(parts)


def _parse(text: str, canary: str, job_input: dict[str, Any]) -> QuestionDraft:
    data = guards.extract_json_object(text, canary)
    data["difficulty"] = job_input["difficulty"]
    data["topics"] = job_input["topics"]
    return QuestionDraft.model_validate(data)


async def run_question_gen(ctx: AppContext, job_input: dict[str, Any]) -> dict[str, Any]:
    nonce, canary = guards.new_nonce(), guards.new_canary()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": guards.build_system_prompt(_PROMPT, nonce, canary)},
        {"role": "user", "content": _user_message(job_input, nonce)},
    ]
    for attempt in range(2):
        reply = await ctx.llm.chat(messages, max_tokens=MAX_TOKENS)
        try:
            draft = _parse(reply.content, canary, job_input)
        except (ValueError, ValidationError) as e:  # ValidationError is a ValueError
            if attempt == 1:
                raise UserFacingError(INVALID_QUESTION) from e
            messages += [
                {"role": "assistant", "content": reply.content},
                {"role": "user", "content": f"That was invalid: {str(e)[:1500]}\nReturn the corrected JSON object only."},
            ]
            continue
        return QuestionGenResult(draft=draft).model_dump(mode="json")
    raise UserFacingError(INVALID_QUESTION)
