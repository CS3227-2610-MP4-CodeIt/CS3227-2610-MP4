"""Code-execution service client (spec §9.2)."""

from collections.abc import Sequence
from typing import Any

import httpx

from app.jobs.runner import UserFacingError
from app.repos.questions import TestCaseRow

JUDGE_BUSY = "The judge is busy. Try again in a moment."
JUDGE_UNAVAILABLE = "The judge is unavailable. Try again."
WALL_GRACE_S = 0.5
QUEUE_TIMEOUT_S = 30


def executor_time_s(n_tests: int, time_limit_ms: int) -> float:
    """Executor spec §10: the longest the executor can take for one request."""
    return n_tests * (time_limit_ms / 1000 + WALL_GRACE_S) + QUEUE_TIMEOUT_S


def http_timeout_s(n_tests: int, time_limit_ms: int) -> float:
    return executor_time_s(n_tests, time_limit_ms) + 5


def job_timeout_s(n_tests: int, time_limit_ms: int) -> float:
    """timeout_s for start_job of run / submit jobs (spec §6.4)."""
    return executor_time_s(n_tests, time_limit_ms) + 10


def build_payload(
    code: str,
    time_limit_ms: int,
    memory_limit_mb: int,
    float_tolerance: dict[str, float] | None,
    test_cases: Sequence[TestCaseRow],
) -> dict[str, Any]:
    return {
        "code": code,
        "time_limit_ms": time_limit_ms,
        "memory_limit_mb": memory_limit_mb,
        "float_tolerance": float_tolerance,
        "test_cases": [{"stdin": t.stdin, "expected_stdout": t.expected_stdout} for t in test_cases],
    }


class ExecutorClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._http = httpx.AsyncClient(base_url=base_url.rstrip("/"), headers={"X-Internal-Token": token})

    async def aclose(self) -> None:
        await self._http.aclose()

    async def execute(
        self,
        code: str,
        time_limit_ms: int,
        memory_limit_mb: int,
        float_tolerance: dict[str, float] | None,
        test_cases: Sequence[TestCaseRow],
    ) -> dict[str, Any]:
        """POST /v1/execute; returns the executor's JSON response (results in test_cases order).
        503 → UserFacingError(JUDGE_BUSY); any other error / timeout → UserFacingError(JUDGE_UNAVAILABLE)."""
        payload = build_payload(code, time_limit_ms, memory_limit_mb, float_tolerance, test_cases)
        try:
            response = await self._http.post(
                "/v1/execute", json=payload, timeout=http_timeout_s(len(test_cases), time_limit_ms)
            )
        except httpx.HTTPError as e:
            raise UserFacingError(JUDGE_UNAVAILABLE) from e
        if response.status_code == 503:
            raise UserFacingError(JUDGE_BUSY)
        if response.status_code != 200:
            raise UserFacingError(JUDGE_UNAVAILABLE)
        try:
            return response.json()
        except ValueError as e:
            raise UserFacingError(JUDGE_UNAVAILABLE) from e
