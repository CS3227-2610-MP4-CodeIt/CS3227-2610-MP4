"""Shared fixtures and builders. Builders are plain functions: `from tests.conftest import question_body`."""

import asyncio
import itertools
import json
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from fastapi import FastAPI

from app.auth import create_session, hash_password
from app.config import AppContext, Settings
from app.db import Database
from app.main import create_app
from app.repos import assignments as assignments_repo
from app.repos import classes as classes_repo
from app.repos import jobs as jobs_repo
from app.repos import questions as questions_repo
from app.repos import users as users_repo
from app.repos.assignments import Assignment
from app.repos.classes import ClassRow
from app.repos.jobs import Job
from app.repos.questions import Question
from app.repos.users import User
from app.schemas import QuestionIn

SOCLAAS_URL = "https://soclaas.test"
EXECUTOR_URL = "https://executor.test"
LLM_MODEL = "coder"
TEST_PASSWORD = "password123"
BOOTSTRAP_ADMIN = ("rootadmin", "rootadmin-pass")

_counter = itertools.count(1)


# --- builders ---------------------------------------------------------------


def question_body(**overrides: Any) -> dict[str, Any]:
    """A valid QuestionIn JSON body (1 visible + 1 hidden test). Override any field."""
    body: dict[str, Any] = {
        "title": "Sum Two",
        "statement_md": "## Problem\nPrint a + b.\n## Input\na b\n## Output\na + b",
        "difficulty": "easy",
        "topics": ["math"],
        "time_limit_ms": 1000,
        "memory_limit_mb": 64,
        "float_tolerance": None,
        "test_cases": [
            {"stdin": "1 2\n", "expected_stdout": "3\n", "is_hidden": False},
            {"stdin": "40 2\n", "expected_stdout": "42\n", "is_hidden": True},
        ],
    }
    body.update(overrides)
    return body


def chat_completion(content: str | None = "", tool_calls: list[dict] | None = None, finish_reason: str | None = None) -> dict:
    """A SoCLaaS /v1/chat/completions response body."""
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "model": "upstream-model",
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason or ("tool_calls" if tool_calls else "stop")}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


def tool_call(name: str, call_id: str = "call_1", arguments: str = "{}") -> dict:
    """One OpenAI-style tool call, for chat_completion(tool_calls=[...])."""
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


def execute_response(statuses: list[str], *, error_message: str | None = None, preview: bool = True) -> dict:
    """An executor /v1/execute response. statuses: one verdict per test, e.g. ["ACCEPTED", "WRONG_ANSWER"].
    Like the executor, it stops at the first failure; previews are added to every result if preview."""
    results: list[dict[str, Any]] = []
    failed: int | None = None
    for i, status in enumerate(statuses):
        result: dict[str, Any] = {"index": i, "status": status, "time_ms": 10 + i, "memory_kb": 9000 + i}
        if preview:
            result["stdout_preview"] = f"out{i}"
            result["stderr_preview"] = f"err{i}"
        results.append(result)
        if status != "ACCEPTED":
            failed = i
            break
    passed = sum(r["status"] == "ACCEPTED" for r in results)
    return {
        "verdict": "ACCEPTED" if failed is None else statuses[failed],
        "passed": passed,
        "total": len(statuses),
        "failed_test_index": failed,
        "error_message": error_message if failed is not None else None,
        "max_time_ms": max(r["time_ms"] for r in results),
        "max_memory_kb": max(r["memory_kb"] for r in results),
        "results": results,
    }


def request_json(call: Any) -> dict:
    """JSON body of a recorded respx call (`route.calls[i]`) or an httpx.Request."""
    request = call.request if hasattr(call, "request") else call
    return json.loads(request.content)


# --- app / client / mocks ---------------------------------------------------


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    return str(tmp_path / "app.db")


@pytest.fixture
def settings(db_path: str) -> Settings:
    """prod-mode settings (no demo seed; tests then start with only the bootstrap admin)."""
    return Settings(
        _env_file=None,  # type: ignore[call-arg]  # never read the real backend/.env
        app_env="prod",
        database_path=db_path,
        bootstrap_admin_username=BOOTSTRAP_ADMIN[0],
        bootstrap_admin_password=BOOTSTRAP_ADMIN[1],
        soclaas_base_url=SOCLAAS_URL,
        soclaas_api_key="test-soclaas-key",
        llm_model=LLM_MODEL,
        llm_job_timeout_s=10,
        code_execution_server=EXECUTOR_URL,
        executor_token="test-executor-token",
    )


@pytest.fixture
def mock_http() -> Iterator[respx.MockRouter]:
    """respx router for all outgoing HTTP. Any unmocked request fails the test (no network).
    Named routes: "models", "llm" (chat completions), "executor" (/v1/execute)."""
    with respx.mock(assert_all_called=False, assert_all_mocked=True) as router:
        router.get(f"{SOCLAAS_URL}/v1/models", name="models").respond(
            json={"object": "list", "data": [{"id": LLM_MODEL, "object": "model"}]}
        )
        router.post(f"{SOCLAAS_URL}/v1/chat/completions", name="llm").respond(json=chat_completion("OK"))
        router.post(f"{EXECUTOR_URL}/v1/execute", name="executor").respond(
            json=execute_response(["ACCEPTED", "ACCEPTED"])
        )
        yield router


@pytest.fixture
def llm_route(mock_http: respx.MockRouter) -> respx.Route:
    """Set replies with `llm_route.side_effect = [httpx.Response(200, json=chat_completion("hi")), ...]`
    or `llm_route.respond(json=...)`; inspect with `request_json(llm_route.calls[0])`."""
    return mock_http["llm"]


@pytest.fixture
def executor_route(mock_http: respx.MockRouter) -> respx.Route:
    return mock_http["executor"]


@pytest.fixture
async def app(settings: Settings, mock_http: respx.MockRouter) -> AsyncIterator[FastAPI]:
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        app.state.ctx.llm.retry_delays_s = (0.0, 0.0)  # no real backoff in tests
        yield app


@pytest.fixture
def ctx(app: FastAPI) -> AppContext:
    return app.state.ctx


@pytest.fixture
def db(ctx: AppContext) -> Database:
    return ctx.db


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30) as c:
        yield c


# --- users / auth -----------------------------------------------------------


@dataclass
class TestUser:
    __test__ = False

    user: User
    password: str
    token: str

    @property
    def id(self) -> int:
        return self.user.id

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


MakeUser = Callable[..., Awaitable[TestUser]]


@pytest.fixture
def make_user(db: Database) -> MakeUser:
    """`await make_user("teacher", username=None, display_name=None, password=TEST_PASSWORD)`:
    creates the user through the repo and a logged-in session (no HTTP)."""

    async def make(role: str, username: str | None = None, display_name: str | None = None, password: str = TEST_PASSWORD) -> TestUser:
        n = next(_counter)
        username = username or f"{role}{n}"
        user = await users_repo.create(db, username, display_name or f"{role.title()} {n}", await hash_password(password), role)
        token = await create_session(db, user.id, 1)
        return TestUser(user, password, token)

    return make


@pytest.fixture
async def admin(make_user: MakeUser) -> TestUser:
    """An extra admin (the bootstrap admin BOOTSTRAP_ADMIN also exists)."""
    return await make_user("admin")


@pytest.fixture
async def teacher(make_user: MakeUser) -> TestUser:
    return await make_user("teacher")


@pytest.fixture
async def student(make_user: MakeUser) -> TestUser:
    return await make_user("student")


@pytest.fixture
def login(client: httpx.AsyncClient) -> Callable[[str, str], Awaitable[dict[str, str]]]:
    """`headers = await login(username, password)` through POST /api/auth/login."""

    async def do_login(username: str, password: str) -> dict[str, str]:
        response = await client.post("/api/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['token']}"}

    return do_login


# --- classes / questions / assignments --------------------------------------


def _id(x: TestUser | int) -> int:
    return x if isinstance(x, int) else x.id


@pytest.fixture
def make_class(db: Database) -> Callable[..., Awaitable[ClassRow]]:
    """`await make_class(members=[teacher, student], name=None)` (members: TestUser or user id)."""

    async def make(members: list[TestUser | int] | None = None, name: str | None = None) -> ClassRow:
        row = await classes_repo.create(db, name or f"Class {next(_counter)}")
        if members:
            await classes_repo.add_members(db, row.id, [_id(m) for m in members])
        found = await classes_repo.get(db, row.id)
        assert found is not None
        return found

    return make


@pytest.fixture
def make_question(db: Database) -> Callable[..., Awaitable[Question]]:
    """`await make_question(owner, **question_body_overrides)` → Question with test_cases."""

    async def make(owner: TestUser | int, **overrides: Any) -> Question:
        return await questions_repo.create(db, _id(owner), QuestionIn.model_validate(question_body(**overrides)))

    return make


@pytest.fixture
def make_assignment(db: Database) -> Callable[..., Awaitable[Assignment]]:
    """`await make_assignment(owner, class_id, [qid, ...], title="Week 1", due_at=None)`."""

    async def make(
        owner: TestUser | int,
        class_id: int,
        question_ids: list[int],
        title: str = "Week 1",
        due_at: datetime | None = None,
        description_md: str = "",
    ) -> Assignment:
        return await assignments_repo.create(db, class_id, _id(owner), title, description_md, due_at, question_ids)

    return make


# --- jobs / SSE -------------------------------------------------------------


@pytest.fixture
def wait_for_job(db: Database) -> Callable[..., Awaitable[Job]]:
    """`job = await wait_for_job(job_id, timeout=5)`: polls until the job is success / failed."""

    async def wait(job_id: int, timeout: float = 5.0) -> Job:
        async with asyncio.timeout(timeout):
            while True:
                job = await jobs_repo.get(db, job_id)
                assert job is not None, f"job {job_id} does not exist"
                if job.status != "in_process":
                    return job
                await asyncio.sleep(0.01)

    return wait


class SSEStream:
    """Drives GET /api/events at the ASGI level (httpx's ASGITransport buffers whole responses)."""

    def __init__(self, app: FastAPI, headers: dict[str, str]) -> None:
        self.app = app
        self.headers = headers
        self.status: int | None = None
        self.response_headers: dict[str, str] = {}
        self._chunks: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._buffer = ""
        self._disconnect = asyncio.Event()
        self._started = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self.ended = False

    async def start(self) -> None:
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/api/events",
            "raw_path": b"/api/events",
            "query_string": b"",
            "root_path": "",
            "headers": [(b"host", b"test")] + [(k.lower().encode(), v.encode()) for k, v in self.headers.items()],
            "client": ("127.0.0.1", 12345),
            "server": ("test", 80),
        }
        sent_request = False

        async def receive() -> dict:
            nonlocal sent_request
            if not sent_request:
                sent_request = True
                return {"type": "http.request", "body": b"", "more_body": False}
            await self._disconnect.wait()
            return {"type": "http.disconnect"}

        async def send(message: dict) -> None:
            if message["type"] == "http.response.start":
                self.status = message["status"]
                self.response_headers = {k.decode(): v.decode() for k, v in message.get("headers", [])}
                self._started.set()
            elif message["type"] == "http.response.body":
                if message.get("body"):
                    await self._chunks.put(message["body"])
                if not message.get("more_body", False):
                    await self._chunks.put(None)

        async def run() -> None:
            try:
                await self.app(scope, receive, send)
            finally:
                self._started.set()
                await self._chunks.put(None)

        self._task = asyncio.create_task(run())
        async with asyncio.timeout(5):
            await self._started.wait()

    async def next_event(self, timeout: float = 5.0) -> tuple[str, dict | None]:
        """Next frame: ("ready", {}), ("job", {...}), ("ping", None), or ("end", None) when the stream closed."""
        async with asyncio.timeout(timeout):
            while "\n\n" not in self._buffer:
                chunk = await self._chunks.get()
                if chunk is None:
                    self.ended = True
                    return "end", None
                self._buffer += chunk.decode()
        frame, self._buffer = self._buffer.split("\n\n", 1)
        if frame.startswith(":"):
            return "ping", None
        fields = dict(line.split(": ", 1) for line in frame.split("\n"))
        return fields["event"], json.loads(fields["data"])

    async def close(self) -> None:
        self._disconnect.set()
        if self._task is not None:
            async with asyncio.timeout(5):
                await asyncio.gather(self._task, return_exceptions=True)


@pytest.fixture
def open_events(app: FastAPI) -> Callable[[dict[str, str]], Any]:
    """`async with open_events(user.headers) as stream: kind, data = await stream.next_event()`."""

    @asynccontextmanager
    async def open_stream(headers: dict[str, str]) -> AsyncIterator[SSEStream]:
        stream = SSEStream(app, headers)
        await stream.start()
        try:
            yield stream
        finally:
            await stream.close()

    return open_stream
