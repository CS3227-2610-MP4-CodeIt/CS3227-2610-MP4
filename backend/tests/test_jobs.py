"""Spec §12.1 (job runner) plus the SoCLaaS / executor clients (§9)."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
import pytest
import respx
from fastapi import Body, Depends, FastAPI

from app.auth import current_user
from app.clients import executor as executor_client
from app.clients.llm import UNAVAILABLE, LLMClient, error_message
from app.config import AppContext, Settings, get_ctx
from app.db import Database
from app.jobs import runner
from app.jobs.runner import UserFacingError, check_job_response, latest_job, new_job_response, start_job
from app.main import create_app
from app.repos import jobs as jobs_repo
from app.repos.questions import TestCaseRow
from app.repos.users import User
from tests.conftest import EXECUTOR_URL, TestUser, chat_completion, execute_response, request_json

Handler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class Probe:
    """A fake long-running feature: POST/GET /api/_probe/{key} with a controllable handler."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.gate = asyncio.Event()
        self.fail_with: BaseException | None = None
        self.timeout_s = 5.0

    async def handler(self, job_input: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(job_input)
        await self.gate.wait()
        if self.fail_with is not None:
            raise self.fail_with
        return {"echo": job_input["code"]}

    def install(self, app: FastAPI) -> None:
        async def new(key: str, body: dict = Body(...), user: User = Depends(current_user), ctx: AppContext = Depends(get_ctx)):
            job, created = await start_job(ctx.db, user.id, "hint", key, body, self.handler, self.timeout_s)
            return new_job_response(job, created)

        async def check(key: str, user: User = Depends(current_user), ctx: AppContext = Depends(get_ctx)):
            return check_job_response(await latest_job(ctx.db, user.id, "hint", key))

        app.add_api_route("/api/_probe/{key}", new, methods=["POST"])
        app.add_api_route("/api/_probe/{key}", check, methods=["GET"])


@pytest.fixture
def probe(app: FastAPI) -> Probe:
    p = Probe()
    p.install(app)
    return p


async def _count_jobs(db: Database) -> int:
    async with db.connect() as conn:
        cursor = await conn.execute("SELECT count(*) FROM jobs")
        return (await cursor.fetchone())[0]  # type: ignore[index]


async def test_new_then_check_while_running(client: httpx.AsyncClient, probe: Probe, student: TestUser, wait_for_job) -> None:
    new = await client.post("/api/_probe/a1:q1", json={"code": "x"}, headers=student.headers)
    assert new.status_code == 202
    body = new.json()
    assert body["created"] is True
    job = body["job"]
    assert set(job) == {"id", "kind", "status", "result", "error", "created_at", "finished_at"}
    assert job["status"] == "in_process" and job["result"] is None and job["finished_at"] is None

    check = await client.get("/api/_probe/a1:q1", headers=student.headers)
    assert check.status_code == 200
    assert check.json() == {"job": job}
    assert "created" not in check.json()

    probe.gate.set()
    finished = await wait_for_job(job["id"])
    assert finished.status == "success"
    assert finished.result == {"echo": "x"}
    assert probe.calls[0]["job_id"] == job["id"]
    check = (await client.get("/api/_probe/a1:q1", headers=student.headers)).json()["job"]
    assert check["status"] == "success" and check["result"] == {"echo": "x"} and check["finished_at"]


async def test_second_new_while_in_process(client: httpx.AsyncClient, probe: Probe, student: TestUser) -> None:
    first = await client.post("/api/_probe/k", json={"code": "one"}, headers=student.headers)
    second = await client.post("/api/_probe/k", json={"code": "two"}, headers=student.headers)
    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json()["created"] is False
    assert second.json()["job"]["id"] == first.json()["job"]["id"]
    await asyncio.sleep(0.05)
    assert len(probe.calls) == 1 and probe.calls[0]["code"] == "one"


async def test_concurrent_new_requests_start_one_job(client: httpx.AsyncClient, db: Database, probe: Probe, student: TestUser) -> None:
    responses = await asyncio.gather(
        *(client.post("/api/_probe/k", json={"code": str(i)}, headers=student.headers) for i in range(10))
    )
    assert sorted(r.status_code for r in responses) == [200] * 9 + [202]
    assert len({r.json()["job"]["id"] for r in responses}) == 1
    assert await _count_jobs(db) == 1
    await asyncio.sleep(0.05)
    assert len(probe.calls) == 1


async def test_new_after_success_and_after_failed(client: httpx.AsyncClient, probe: Probe, student: TestUser, wait_for_job) -> None:
    probe.gate.set()
    first = (await client.post("/api/_probe/k", json={"code": "a"}, headers=student.headers)).json()["job"]
    assert (await wait_for_job(first["id"])).status == "success"

    probe.fail_with = RuntimeError("boom")
    second = await client.post("/api/_probe/k", json={"code": "b"}, headers=student.headers)
    assert second.status_code == 202 and second.json()["job"]["id"] != first["id"]
    assert (await wait_for_job(second.json()["job"]["id"])).status == "failed"

    probe.fail_with = None
    third = await client.post("/api/_probe/k", json={"code": "c"}, headers=student.headers)
    assert third.status_code == 202
    assert (await wait_for_job(third.json()["job"]["id"])).status == "success"


async def test_different_keys_run_in_parallel(client: httpx.AsyncClient, db: Database, probe: Probe, student: TestUser) -> None:
    q1 = await client.post("/api/_probe/a1:q1", json={"code": "x"}, headers=student.headers)
    q2 = await client.post("/api/_probe/a1:q2", json={"code": "y"}, headers=student.headers)
    assert q1.status_code == q2.status_code == 202
    await asyncio.sleep(0.05)
    assert len(probe.calls) == 2
    for response in (q1, q2):
        job = await jobs_repo.get(db, response.json()["job"]["id"])
        assert job is not None and job.status == "in_process"


async def test_same_key_other_user_is_separate(client: httpx.AsyncClient, probe: Probe, student: TestUser, make_user) -> None:
    other = await make_user("student")
    a = await client.post("/api/_probe/k", json={"code": "x"}, headers=student.headers)
    b = await client.post("/api/_probe/k", json={"code": "y"}, headers=other.headers)
    assert a.status_code == b.status_code == 202
    assert a.json()["job"]["id"] != b.json()["job"]["id"]


async def test_check_with_no_job(client: httpx.AsyncClient, probe: Probe, student: TestUser) -> None:
    response = await client.get("/api/_probe/never", headers=student.headers)
    assert response.status_code == 200
    assert response.json() == {"job": None}


async def test_client_disconnect_does_not_cancel_job(app: FastAPI, probe: Probe, student: TestUser, wait_for_job) -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as short_lived:
        job_id = (await short_lived.post("/api/_probe/k", json={"code": "x"}, headers=student.headers)).json()["job"]["id"]
    probe.gate.set()
    assert (await wait_for_job(job_id)).status == "success"


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (RuntimeError("secret /etc/passwd Traceback"), runner.GENERIC_ERROR),
        (UserFacingError("The judge is busy. Try again in a moment."), "The judge is busy. Try again in a moment."),
    ],
)
async def test_handler_raises(client: httpx.AsyncClient, probe: Probe, student: TestUser, wait_for_job, error: Exception, expected: str) -> None:
    probe.fail_with = error
    probe.gate.set()
    job_id = (await client.post("/api/_probe/k", json={"code": "x"}, headers=student.headers)).json()["job"]["id"]
    job = await wait_for_job(job_id)
    assert job.status == "failed"
    assert job.error == expected
    assert job.result is None and job.finished_at is not None


async def test_handler_times_out(client: httpx.AsyncClient, probe: Probe, student: TestUser, wait_for_job) -> None:
    probe.timeout_s = 0.05  # gate never opens
    job_id = (await client.post("/api/_probe/k", json={"code": "x"}, headers=student.headers)).json()["job"]["id"]
    job = await wait_for_job(job_id)
    assert job.status == "failed"
    assert job.error == runner.TIMEOUT_ERROR


async def test_restart_fails_in_process_jobs(settings: Settings, db: Database, student: TestUser) -> None:
    stale = await jobs_repo.insert_in_process(db, student.id, "hint", "k", {"code": "x"})

    second_app = create_app(settings)
    async with second_app.router.lifespan_context(second_app):
        job = await jobs_repo.get(db, stale.id)
        assert job is not None and job.status == "failed" and job.error == runner.RESTART_ERROR

        async def handler(job_input: dict[str, Any]) -> dict[str, Any]:
            return {}

        new_job, created = await start_job(db, student.id, "hint", "k", {"code": "y"}, handler, 5)
        assert created and new_job.id != stale.id


async def test_shutdown_fails_running_jobs(settings: Settings, db: Database, student: TestUser) -> None:
    second_app = create_app(settings)
    async with second_app.router.lifespan_context(second_app):
        never = asyncio.Event()

        async def handler(job_input: dict[str, Any]) -> dict[str, Any]:
            await never.wait()
            return {}

        job, _ = await start_job(db, student.id, "hint", "k", {}, handler, 60)
    finished = await jobs_repo.get(db, job.id)
    assert finished is not None and finished.status == "failed" and finished.error == runner.RESTART_ERROR


async def test_event_loop_not_blocked_by_llm_call(
    app: FastAPI, client: httpx.AsyncClient, ctx: AppContext, llm_route: respx.Route, student: TestUser
) -> None:
    async def slow(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(5)
        return httpx.Response(200, json=chat_completion("late"))

    llm_route.side_effect = slow

    async def handler(job_input: dict[str, Any]) -> dict[str, Any]:
        reply = await ctx.llm.chat([{"role": "user", "content": "hi"}])
        return {"text": reply.content}

    await start_job(ctx.db, student.id, "hint", "k", {}, handler, 30)
    await asyncio.sleep(0.05)  # the LLM call is now in flight
    started = time.perf_counter()
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert time.perf_counter() - started < 0.1


# --- clients ----------------------------------------------------------------


async def test_llm_retries_429_then_succeeds(ctx: AppContext, llm_route: respx.Route, student: TestUser, wait_for_job) -> None:
    llm_route.side_effect = [
        httpx.Response(429, json={"error": "rate limit exceeded"}),
        httpx.Response(200, json=chat_completion("\n\nhello ")),
    ]

    async def handler(job_input: dict[str, Any]) -> dict[str, Any]:
        reply = await ctx.llm.chat([{"role": "user", "content": "hi"}], max_tokens=50)
        return {"text": reply.content}

    job, _ = await start_job(ctx.db, student.id, "hint", "k", {}, handler, 5)
    finished = await wait_for_job(job.id)
    assert finished.status == "success" and finished.result == {"text": "hello"}
    assert llm_route.call_count == 2
    sent = request_json(llm_route.calls[0])
    assert sent["model"] == "coder" and sent["max_tokens"] == 50
    assert llm_route.calls[0].request.headers["authorization"] == "Bearer test-soclaas-key"


async def test_llm_gives_up_after_two_retries(ctx: AppContext, llm_route: respx.Route) -> None:
    llm_route.side_effect = [httpx.Response(503, json={"error": "busy"})] * 3
    with pytest.raises(UserFacingError, match=UNAVAILABLE):
        await ctx.llm.chat([{"role": "user", "content": "hi"}])
    assert llm_route.call_count == 3


async def test_llm_other_errors_are_not_retried(ctx: AppContext, llm_route: respx.Route) -> None:
    llm_route.side_effect = [httpx.Response(400, json={"error": {"message": "bad", "type": "x"}})]
    with pytest.raises(UserFacingError, match=UNAVAILABLE):
        await ctx.llm.chat([{"role": "user", "content": "hi"}])
    assert llm_route.call_count == 1


async def test_llm_tool_calls_are_returned(ctx: AppContext, llm_route: respx.Route) -> None:
    call = {"id": "c1", "type": "function", "function": {"name": "get_code", "arguments": "{}"}}
    llm_route.respond(json=chat_completion(None, tool_calls=[call]))
    reply = await ctx.llm.chat([{"role": "user", "content": "hi"}], tools=[], tool_choice="auto")
    assert reply.content == "" and reply.tool_calls == [call] and reply.finish_reason == "tool_calls"
    assert reply.assistant_message() == {"role": "assistant", "content": "", "tool_calls": [call]}


def test_error_message_parses_both_shapes() -> None:
    assert error_message(httpx.Response(429, json={"error": "rate limit"})) == "rate limit"
    assert error_message(httpx.Response(400, json={"error": {"message": "unknown id", "code": "x"}})) == "unknown id"


async def test_startup_fails_for_unknown_model(settings: Settings, mock_http: respx.MockRouter) -> None:
    mock_http["models"].respond(json={"object": "list", "data": [{"id": "other"}]})
    bad_app = create_app(settings)
    with pytest.raises(RuntimeError, match="LLM_MODEL"):
        async with bad_app.router.lifespan_context(bad_app):
            pass


async def test_prod_refuses_http_executor(settings: Settings) -> None:
    bad_app = create_app(settings.model_copy(update={"code_execution_server": "http://executor.test"}))
    with pytest.raises(RuntimeError, match="https"):
        async with bad_app.router.lifespan_context(bad_app):
            pass


def test_executor_timeouts() -> None:
    assert executor_client.http_timeout_s(4, 2000) == 4 * 2.5 + 30 + 5
    assert executor_client.job_timeout_s(4, 2000) == 4 * 2.5 + 30 + 10


async def test_executor_client(ctx: AppContext, executor_route: respx.Route) -> None:
    tests = [TestCaseRow(1, 1, False, "1\n", "1\n"), TestCaseRow(2, 2, True, "2\n", "2\n")]
    executor_route.respond(json=execute_response(["ACCEPTED", "WRONG_ANSWER"]))
    result = await ctx.executor.execute("print(1)", 1000, 64, None, tests)
    assert result["verdict"] == "WRONG_ANSWER"
    sent = request_json(executor_route.calls[0])
    assert sent == {
        "code": "print(1)",
        "time_limit_ms": 1000,
        "memory_limit_mb": 64,
        "float_tolerance": None,
        "test_cases": [{"stdin": "1\n", "expected_stdout": "1\n"}, {"stdin": "2\n", "expected_stdout": "2\n"}],
    }
    assert executor_route.calls[0].request.headers["x-internal-token"] == "test-executor-token"
    assert str(executor_route.calls[0].request.url) == f"{EXECUTOR_URL}/v1/execute"

    executor_route.respond(503, json={"detail": "All execution slots are busy"})
    with pytest.raises(UserFacingError, match="busy"):
        await ctx.executor.execute("print(1)", 1000, 64, None, tests)

    executor_route.side_effect = httpx.ConnectTimeout("timeout")
    with pytest.raises(UserFacingError, match="unavailable"):
        await ctx.executor.execute("print(1)", 1000, 64, None, tests)



@pytest.mark.parametrize("base_url", ["https://gw.test", "https://gw.test/", "https://gw.test/v1", "https://gw.test/v1/"])
async def test_llm_urls_have_a_single_v1(base_url: str) -> None:
    with respx.mock(assert_all_mocked=True) as router:  # exact URLs: a doubled /v1 is unmocked and fails
        models = router.get("https://gw.test/v1/models").respond(json={"data": [{"id": "coder"}]})
        chat = router.post("https://gw.test/v1/chat/completions").respond(json=chat_completion("hi"))
        llm = LLMClient(base_url, "key", "coder", 300, retry_delays_s=())
        try:
            await llm.check_model()
            assert (await llm.chat([{"role": "user", "content": "x"}])).content == "hi"
        finally:
            await llm.aclose()
    assert str(models.calls[0].request.url) == "https://gw.test/v1/models"
    assert str(chat.calls[0].request.url) == "https://gw.test/v1/chat/completions"
