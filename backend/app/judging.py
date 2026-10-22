"""Run and submit handlers (spec §7.4)."""

from typing import Any

from app.config import AppContext
from app.jobs.runner import UserFacingError
from app.repos import questions as questions_repo
from app.repos import submissions as submissions_repo
from app.schemas import JudgeResult


async def run_judge(ctx: AppContext, job_input: dict[str, Any]) -> dict[str, Any]:
    """Handler for kind 'run' (visible tests) and 'submit' (all tests, visible first)."""
    submit: bool = job_input["submit"]
    question = await questions_repo.get(ctx.db, job_input["question_id"])
    if question is None:
        raise UserFacingError("The question no longer exists.")
    tests = sorted(question.test_cases, key=lambda t: (t.is_hidden, t.position))
    if not submit:
        tests = [t for t in tests if not t.is_hidden]

    response = await ctx.executor.execute(
        job_input["code"], question.time_limit_ms, question.memory_limit_mb, question.float_tolerance, tests
    )
    try:
        result = _redact(response, [t.is_hidden for t in tests])
    except (KeyError, TypeError, ValueError) as e:
        raise UserFacingError("The judge is unavailable. Try again.") from e

    if submit:
        await submissions_repo.create(
            ctx.db, job_input["student_id"], job_input["assignment_id"], job_input["question_id"],
            job_input["job_id"], job_input["code"], result["verdict"], result["passed"], result["total"],
        )
    return result


def _redact(response: dict[str, Any], hidden_flags: list[bool]) -> dict[str, Any]:
    results = []
    for r in response["results"]:
        hidden = hidden_flags[r["index"]]
        item = {k: r.get(k) for k in ("index", "status", "time_ms", "memory_kb")}
        item["hidden"] = hidden
        if not hidden:
            item["stdout_preview"] = r.get("stdout_preview")
            item["stderr_preview"] = r.get("stderr_preview")
        results.append(item)
    failed = response.get("failed_test_index")
    error_message = response.get("error_message")
    if failed is not None and hidden_flags[failed]:
        error_message = None
    data = {
        "verdict": response["verdict"], "passed": response["passed"], "total": response["total"],
        "failed_test_index": failed, "error_message": error_message,
        "max_time_ms": response["max_time_ms"], "max_memory_kb": response.get("max_memory_kb"),
        "results": results,
    }
    return JudgeResult.model_validate(data).model_dump()
