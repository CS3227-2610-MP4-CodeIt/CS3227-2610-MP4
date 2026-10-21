import asyncio
import shutil
import signal
import tempfile
from pathlib import Path

from app.compare import compare
from app.config import Settings
from app.runner import RunResult, run_test
from app.sanitize import head, sanitize_traceback, tail
from app.schemas import ExecuteRequest, ExecuteResponse, TestResult, Verdict

PREVIEW_BYTES = 1024


def classify(result: RunResult, req: ExecuteRequest, expected_stdout: str, workdir: str) -> tuple[Verdict, str | None]:
    """Spec §4.1: the first matching rule wins."""
    report = result.report or {}
    if result.timed_out:
        return Verdict.TIME_LIMIT_EXCEEDED, "Time limit exceeded"
    if result.signal == signal.SIGXCPU or report.get("status") == "cpu":
        return Verdict.TIME_LIMIT_EXCEEDED, "Time limit exceeded"
    if report.get("status") == "memory" or (
        result.peak_rss_kb is not None and result.peak_rss_kb > req.memory_limit_mb * 1024
    ):
        return Verdict.MEMORY_LIMIT_EXCEEDED, "Memory limit exceeded"
    if result.output_limit_exceeded:
        return Verdict.RUNTIME_ERROR, "Output limit exceeded"
    if result.signal is not None:
        return Verdict.RUNTIME_ERROR, f"Killed by signal {signal.Signals(result.signal).name}"
    if result.exit_code != 0:
        message = sanitize_traceback(result.stderr, workdir).strip()
        if not message:
            code = report.get("code", result.exit_code)
            message = f"Exited with code {code}"
        return Verdict.RUNTIME_ERROR, message
    if result.time_ms > req.time_limit_ms:
        return Verdict.TIME_LIMIT_EXCEEDED, "Time limit exceeded"
    mismatch = compare(result.stdout, expected_stdout, req.float_tolerance)
    if mismatch is not None:
        return Verdict.WRONG_ANSWER, mismatch
    return Verdict.ACCEPTED, None


async def run_job(req: ExecuteRequest, settings: Settings) -> ExecuteResponse:
    workdir = await asyncio.to_thread(tempfile.mkdtemp, dir=settings.work_root)  # mode 0o700
    try:
        Path(workdir, "solution.py").write_text(req.code, encoding="utf-8")
        results: list[TestResult] = []
        verdict, error_message, failed_index = Verdict.ACCEPTED, None, None

        for index, test in enumerate(req.test_cases):
            run = await run_test(
                workdir, test.stdin, test.expected_stdout, req.time_limit_ms, req.memory_limit_mb, settings
            )
            status, message = classify(run, req, test.expected_stdout, workdir)
            result = TestResult(index=index, status=status, time_ms=run.time_ms, memory_kb=run.peak_rss_kb)
            if status != Verdict.ACCEPTED:
                result.stdout_preview = head(run.stdout.decode("utf-8", errors="replace"), PREVIEW_BYTES)
                result.stderr_preview = tail(sanitize_traceback(run.stderr, workdir), PREVIEW_BYTES)
                verdict, error_message, failed_index = status, message, index
            results.append(result)
            if status != Verdict.ACCEPTED:
                break
    finally:
        await asyncio.to_thread(shutil.rmtree, workdir, ignore_errors=True)

    memories = [r.memory_kb for r in results if r.memory_kb is not None]
    return ExecuteResponse(
        verdict=verdict,
        passed=sum(r.status == Verdict.ACCEPTED for r in results),
        total=len(req.test_cases),
        failed_test_index=failed_index,
        error_message=error_message,
        max_time_ms=max(r.time_ms for r in results),
        max_memory_kb=max(memories) if memories else None,
        results=results,
    )
