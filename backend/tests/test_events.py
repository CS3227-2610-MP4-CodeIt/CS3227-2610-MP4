"""Spec §12.2: SSE job notifications."""

import asyncio
from typing import Any

import httpx
import pytest

from app.auth import token_hash
from app.db import Database
from app.jobs import events
from app.jobs.runner import start_job
from app.repos import users as users_repo
from app.routers import events as events_router
from tests.conftest import TestUser


def _handler(gate: asyncio.Event):
    async def handler(job_input: dict[str, Any]) -> dict[str, Any]:
        await gate.wait()
        return {"ok": True}

    return handler


async def test_first_event_is_ready(open_events, student: TestUser) -> None:
    async with open_events(student.headers) as stream:
        assert stream.status == 200
        assert await stream.next_event() == ("ready", {})


async def test_stream_headers(open_events, student: TestUser) -> None:
    async with open_events(student.headers) as stream:
        assert stream.response_headers["content-type"].startswith("text/event-stream")
        assert stream.response_headers["cache-control"] == "no-cache"
        assert stream.response_headers["x-accel-buffering"] == "no"


async def test_no_or_bad_token_is_401(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/events")).status_code == 401
    assert (await client.get("/api/events", headers={"Authorization": "Bearer nope"})).status_code == 401


async def test_job_created_and_finished_events(open_events, db: Database, student: TestUser) -> None:
    gate = asyncio.Event()
    async with open_events(student.headers) as stream:
        assert (await stream.next_event())[0] == "ready"
        job, _ = await start_job(db, student.id, "hint", "a1:q2", {"code": "x"}, _handler(gate), 5)
        created = await stream.next_event()
        gate.set()
        finished = await stream.next_event()
    expected = ("job", {"job_id": job.id, "kind": "hint", "target_key": "a1:q2"})
    assert created == expected
    assert finished == expected  # only ids: no status, result or error


async def test_only_owner_gets_events(open_events, db: Database, student: TestUser, make_user) -> None:
    other = await make_user("student")
    gate = asyncio.Event()
    gate.set()
    async with open_events(student.headers) as mine, open_events(other.headers) as theirs:
        await mine.next_event()
        await theirs.next_event()
        job, _ = await start_job(db, student.id, "hint", "k", {}, _handler(gate), 5)
        assert (await mine.next_event())[1]["job_id"] == job.id  # type: ignore[index]
        assert (await mine.next_event())[1]["job_id"] == job.id  # type: ignore[index]
        with pytest.raises(TimeoutError):
            await theirs.next_event(timeout=0.2)


async def test_two_streams_of_one_user_both_get_events(open_events, db: Database, student: TestUser) -> None:
    gate = asyncio.Event()
    async with open_events(student.headers) as tab1, open_events(student.headers) as tab2:
        await tab1.next_event()
        await tab2.next_event()
        assert events.subscriber_count(student.id) == 2
        job, _ = await start_job(db, student.id, "hint", "k", {}, _handler(gate), 5)
        assert (await tab1.next_event())[1]["job_id"] == job.id  # type: ignore[index]
        assert (await tab2.next_event())[1]["job_id"] == job.id  # type: ignore[index]
        gate.set()


async def test_closed_stream_is_removed(open_events, student: TestUser) -> None:
    async with open_events(student.headers) as stream:
        await stream.next_event()
        assert events.subscriber_count(student.id) == 1
    assert events.subscriber_count(student.id) == 0


async def test_full_queue_does_not_block(db: Database, student: TestUser, wait_for_job) -> None:
    queue = events.subscribe(student.id)  # a client that never reads
    try:
        gate = asyncio.Event()
        gate.set()
        for _ in range(101):
            job, _ = await start_job(db, student.id, "hint", "k", {}, _handler(gate), 5)
            assert (await wait_for_job(job.id)).status == "success"
        assert queue.qsize() == events.QUEUE_SIZE
    finally:
        events.unsubscribe(student.id, queue)


async def test_stream_ends_when_session_deleted(
    open_events, db: Database, student: TestUser, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(events_router, "PING_INTERVAL_S", 0.1)
    async with open_events(student.headers) as stream:
        assert (await stream.next_event())[0] == "ready"
        assert (await stream.next_event())[0] == "ping"
        await users_repo.delete_session(db, token_hash(student.token))
        while True:
            event = await stream.next_event()
            if event == ("end", None):
                break
            assert event == ("ping", None)
    assert events.subscriber_count(student.id) == 0


async def test_shutdown_closes_streams(open_events, student: TestUser) -> None:
    async with open_events(student.headers) as stream:
        await stream.next_event()
        events.close_all()
        assert await stream.next_event() == ("end", None)
