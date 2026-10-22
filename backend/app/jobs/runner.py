"""Generic job state machine (spec §6) used by every long-running feature."""

import asyncio
import sqlite3
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi.responses import JSONResponse

from app.db import Database
from app.jobs import events
from app.repos import jobs as jobs_repo
from app.repos.jobs import Job
from app.schemas import JobCheckOut, JobNewOut, JobOut

# handler(job_input) -> result dict. job_input is the stored input plus "job_id" (the job's id).
Handler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]

TIMEOUT_ERROR = "The request took too long. Try again."
GENERIC_ERROR = "Something went wrong. Try again."
RESTART_ERROR = "Interrupted by a server restart. Try again."

_tasks: set[asyncio.Task[None]] = set()


class UserFacingError(Exception):
    """Raised by handlers / clients; its message (short, safe) becomes the job's `error`."""


async def start_job(
    db: Database,
    user_id: int,
    kind: str,
    target_key: str,
    job_input: dict[str, Any],
    handler: Handler,
    timeout_s: float,
) -> tuple[Job, bool]:
    """Starts a job unless one for (user_id, kind, target_key) is in process.
    Returns (job, created); when created is False the existing in-process job is returned."""
    try:
        job = await jobs_repo.insert_in_process(db, user_id, kind, target_key, job_input)
    except sqlite3.IntegrityError:
        existing = await jobs_repo.get_in_process(db, user_id, kind, target_key)
        if existing is not None:
            return existing, False
        job = await jobs_repo.insert_in_process(db, user_id, kind, target_key, job_input)  # finished in between
    events.publish(job)
    task = asyncio.create_task(_run(db, job, handler, timeout_s))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job, True


async def _run(db: Database, job: Job, handler: Handler, timeout_s: float) -> None:
    try:
        async with asyncio.timeout(timeout_s):
            result = await handler({**job.input, "job_id": job.id})
        await _finish(db, job, "success", result=result)
    except UserFacingError as e:
        await _finish(db, job, "failed", error=str(e) or GENERIC_ERROR)
    except TimeoutError:
        await _finish(db, job, "failed", error=TIMEOUT_ERROR)
    except Exception:
        await _finish(db, job, "failed", error=GENERIC_ERROR)


async def _finish(db: Database, job: Job, status: str, *, result: dict[str, Any] | None = None, error: str | None = None) -> None:
    await jobs_repo.finish(db, job.id, status, result=result, error=error)
    events.publish(job)  # only after the DB write is committed


async def latest_job(db: Database, user_id: int, kind: str, target_key: str) -> Job | None:
    """For "check" endpoints. Never starts a job."""
    return await jobs_repo.latest(db, user_id, kind, target_key)


def job_out(job: Job) -> JobOut:
    return JobOut.model_validate(job)


def new_job_response(job: Job, created: bool) -> JSONResponse:
    """Response of a "new" endpoint: 202 {"created": true, ...} or 200 {"created": false, ...}."""
    body = JobNewOut(created=created, job=job_out(job))
    return JSONResponse(body.model_dump(mode="json"), status_code=202 if created else 200)


def check_job_response(job: Job | None) -> JobCheckOut:
    """Response of a "check" endpoint: {"job": {...}} or {"job": null}."""
    return JobCheckOut(job=job_out(job) if job else None)


async def recover(db: Database) -> None:
    """Startup: jobs left in_process belong to a dead process."""
    await jobs_repo.fail_all_in_process(db, RESTART_ERROR)


async def shutdown(db: Database) -> None:
    """Lifespan exit: cancel running jobs, wait for them, mark them failed."""
    tasks = list(_tasks)
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    for job in await jobs_repo.fail_all_in_process(db, RESTART_ERROR):
        events.publish(job)
