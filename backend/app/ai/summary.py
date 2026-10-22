import json
from pathlib import Path

from app.ai import guards
from app.config import AppContext
from app.jobs.runner import UserFacingError
from app.repos import submissions as submissions_repo

SUMMARY_MAX_TOKENS = 500
_PROMPT = Path(__file__).parent / "prompts" / "summary.md"


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
    return {"stats": stats, "summary_md": guards.check_summary_output(reply.content, canary)}
