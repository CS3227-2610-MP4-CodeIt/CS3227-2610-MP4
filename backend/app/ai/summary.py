import json
import logging
from pathlib import Path

from app.ai import guards
from app.clients.llm import ChatReply
from app.config import AppContext
from app.jobs.runner import UserFacingError
from app.repos import submissions as submissions_repo

SUMMARY_MAX_TOKENS = 768
_SUMMARY_MAX_WORDS = 250
_SUMMARY_REJECTED = "The AI summary response was rejected. Try again."
_PROMPT = Path(__file__).parent / "prompts" / "summary.md"
logger = logging.getLogger(__name__)


def _validate_summary_reply(reply: ChatReply, canary: str) -> str:
    try:
        guards.check_canary(reply.content, canary)
    except UserFacingError:
        logger.warning("Admin summary validation rejected: canary_detected")
        raise
    # Fixed literals only: never log response text, tool arguments or provider metadata.
    if reply.finish_reason != "stop":
        if reply.finish_reason == "length":
            logger.warning("Admin summary validation rejected: finish_length")
        elif reply.finish_reason is None:
            logger.warning("Admin summary validation rejected: finish_missing")
        else:
            logger.warning("Admin summary validation rejected: finish_other")
        raise UserFacingError(_SUMMARY_REJECTED)
    if reply.tool_calls:
        logger.warning("Admin summary validation rejected: unexpected_tools")
        raise UserFacingError(_SUMMARY_REJECTED)
    text = reply.content.strip()
    if not text:
        logger.warning("Admin summary validation rejected: empty")
        raise UserFacingError(_SUMMARY_REJECTED)
    if len(text.split()) > _SUMMARY_MAX_WORDS:
        logger.warning("Admin summary validation rejected: word_limit")
        raise UserFacingError(_SUMMARY_REJECTED)
    if len(text) > guards.MAX_SUMMARY_CHARS:
        logger.warning("Admin summary validation rejected: character_limit")
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
