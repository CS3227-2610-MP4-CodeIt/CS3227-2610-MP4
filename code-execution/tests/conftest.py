from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from app.config import Settings
from app.main import create_app

TOKEN = "test-token"
AUTH = {"X-Internal-Token": TOKEN}


def job(code: str, tests: list[tuple[str, str]] | None = None, **overrides: Any) -> dict:
    """Build a request body; `tests` is a list of (stdin, expected_stdout)."""
    tests = tests if tests is not None else [("", "")]
    body = {
        "code": code,
        "time_limit_ms": 1000,
        "memory_limit_mb": 64,
        "test_cases": [{"stdin": i, "expected_stdout": o} for i, o in tests],
    }
    body.update(overrides)
    return body


@pytest.fixture
def work_root(tmp_path: Path) -> Path:
    return tmp_path / "work"


@pytest.fixture
def settings(work_root: Path) -> Settings:
    return Settings(executor_token=TOKEN, work_root=str(work_root))


@pytest.fixture
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        yield app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=60) as c:
        yield c


@pytest.fixture
def execute(client: httpx.AsyncClient):
    async def run(body: dict) -> dict:
        response = await client.post("/v1/execute", json=body, headers=AUTH)
        assert response.status_code == 200, response.text
        return response.json()

    return run
