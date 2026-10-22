import json
from dataclasses import dataclass
from typing import Any

import aiosqlite

from app.db import Database

_COLUMNS = "id, user_id, kind, target_key, status, input_json, result_json, error, created_at, finished_at"


@dataclass
class Job:
    id: int
    user_id: int
    kind: str
    target_key: str
    status: str  # in_process / success / failed
    input: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    created_at: str
    finished_at: str | None


def _job(row: aiosqlite.Row) -> Job:
    return Job(
        id=row["id"],
        user_id=row["user_id"],
        kind=row["kind"],
        target_key=row["target_key"],
        status=row["status"],
        input=json.loads(row["input_json"]),
        result=json.loads(row["result_json"]) if row["result_json"] is not None else None,
        error=row["error"],
        created_at=row["created_at"],
        finished_at=row["finished_at"],
    )


async def insert_in_process(db: Database, user_id: int, kind: str, target_key: str, job_input: dict[str, Any]) -> Job:
    """Raises sqlite3.IntegrityError if a job for this key is already in process."""
    async with db.transaction() as conn:
        cursor = await conn.execute(
            f"INSERT INTO jobs (user_id, kind, target_key, input_json) VALUES (?, ?, ?, ?) RETURNING {_COLUMNS}",
            (user_id, kind, target_key, json.dumps(job_input)),
        )
        row = await cursor.fetchone()
        await cursor.close()
    assert row is not None
    return _job(row)


async def get(db: Database, job_id: int) -> Job | None:
    async with db.connect() as conn:
        cursor = await conn.execute(f"SELECT {_COLUMNS} FROM jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
    return _job(row) if row else None


async def get_in_process(db: Database, user_id: int, kind: str, target_key: str) -> Job | None:
    async with db.connect() as conn:
        cursor = await conn.execute(
            f"SELECT {_COLUMNS} FROM jobs WHERE user_id = ? AND kind = ? AND target_key = ? AND status = 'in_process'",
            (user_id, kind, target_key),
        )
        row = await cursor.fetchone()
    return _job(row) if row else None


async def latest(db: Database, user_id: int, kind: str, target_key: str) -> Job | None:
    async with db.connect() as conn:
        cursor = await conn.execute(
            f"SELECT {_COLUMNS} FROM jobs WHERE user_id = ? AND kind = ? AND target_key = ? ORDER BY id DESC LIMIT 1",
            (user_id, kind, target_key),
        )
        row = await cursor.fetchone()
    return _job(row) if row else None


async def finish(
    db: Database, job_id: int, status: str, *, result: dict[str, Any] | None = None, error: str | None = None
) -> None:
    """Moves an in_process job to success (with result) or failed (with error). No-op otherwise."""
    async with db.transaction() as conn:
        await conn.execute(
            "UPDATE jobs SET status = ?, result_json = ?, error = ?, "
            "finished_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ? AND status = 'in_process'",
            (status, json.dumps(result) if result is not None else None, error, job_id),
        )


async def fail_all_in_process(db: Database, error: str) -> list[Job]:
    """Marks every in_process job failed (startup / shutdown recovery). Returns those jobs."""
    async with db.transaction() as conn:
        cursor = await conn.execute(
            "UPDATE jobs SET status = 'failed', error = ?, finished_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') "
            f"WHERE status = 'in_process' RETURNING {_COLUMNS}",
            (error,),
        )
        rows = await cursor.fetchall()
        await cursor.close()
    return [_job(row) for row in rows]
