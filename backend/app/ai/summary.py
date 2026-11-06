import json
from pathlib import Path

from app.ai import guards
from app.clients.llm import ChatReply
from app.config import AppContext
from app.jobs.runner import UserFacingError
from app.repos import submissions as submissions_repo

SUMMARY_MAX_TOKENS = 512
_SUMMARY_MAX_WORDS = 150
_SUMMARY_REJECTED = "The AI summary response was rejected. Try again."
_PROMPT = Path(__file__).parent / "prompts" / "summary.md"


def _validate_summary_reply(reply: ChatReply, canary: str) -> str:
    guards.check_canary(reply.content, canary)
    if reply.finish_reason != "stop" or reply.tool_calls:
        raise UserFacingError(_SUMMARY_REJECTED)
    text = reply.content.strip()
    if not text or len(text.split()) > _SUMMARY_MAX_WORDS or len(text) > guards.MAX_SUMMARY_CHARS:
        raise UserFacingError(_SUMMARY_REJECTED)
    return text


async def run_summary(ctx: AppContext, job_input: dict) -> dict:
    stats = await submissions_repo.assignment_stats(ctx.db, job_input["assignment_id"])
    if stats is None:
        raise UserFacingError("Assignment not found.")
    nonce = guards.new_nonce()
    canary = guards.new_canary()
    system = guards.build_system_prompt(_PROMPT.read_text(), nonce, canary)
    data = guards.wrap_untrusted("stats", json.dumps(stats), nonce)
    reply = await ctx.llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": data}],
        max_tokens=SUMMARY_MAX_TOKENS,
    )
    return {"stats": stats, "summary_md": _validate_summary_reply(reply, canary)}
