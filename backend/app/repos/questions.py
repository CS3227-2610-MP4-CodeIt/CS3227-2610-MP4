import json
import sqlite3
from dataclasses import dataclass, field

import aiosqlite

from app.db import Database, now_iso
from app.repos import Conflict
from app.schemas import QuestionIn

_COLUMNS = (
    "id, created_by, title, statement_md, difficulty, topics_json, time_limit_ms, memory_limit_mb, "
    "float_abs, float_rel, source_job_id, created_at, updated_at"
)


@dataclass
class TestCaseRow:
    __test__ = False

    id: int
    position: int
    is_hidden: bool
    stdin: str
    expected_stdout: str


@dataclass
class Question:
    id: int
    created_by: int | None
    title: str
    statement_md: str
    difficulty: str
    topics: list[str]
    time_limit_ms: int
    memory_limit_mb: int
    float_tolerance: dict[str, float] | None  # {"abs": .., "rel": ..} or None (exact)
    source_job_id: int | None
    created_at: str
    updated_at: str
    test_cases: list[TestCaseRow] = field(default_factory=list)  # empty unless loaded


def _question(row: aiosqlite.Row) -> Question:
    tolerance = None if row["float_abs"] is None else {"abs": row["float_abs"], "rel": row["float_rel"]}
    return Question(
        id=row["id"],
        created_by=row["created_by"],
        title=row["title"],
        statement_md=row["statement_md"],
        difficulty=row["difficulty"],
        topics=json.loads(row["topics_json"]),
        time_limit_ms=row["time_limit_ms"],
        memory_limit_mb=row["memory_limit_mb"],
        float_tolerance=tolerance,
        source_job_id=row["source_job_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _fields(data: QuestionIn) -> tuple:
    tol = data.float_tolerance
    return (
        data.title,
        data.statement_md,
        data.difficulty,
        json.dumps(data.topics),
        data.time_limit_ms,
        data.memory_limit_mb,
        tol.abs if tol else None,
        tol.rel if tol else None,
    )


async def _insert_tests(conn: aiosqlite.Connection, question_id: int, data: QuestionIn) -> None:
    await conn.executemany(
        "INSERT INTO test_cases (question_id, position, is_hidden, stdin, expected_stdout) VALUES (?, ?, ?, ?, ?)",
        [(question_id, i, int(t.is_hidden), t.stdin, t.expected_stdout) for i, t in enumerate(data.test_cases, 1)],
    )


async def create(db: Database, created_by: int, data: QuestionIn, source_job_id: int | None = None) -> Question:
    """Inserts the question and its test cases (position = list order, from 1).
    Raises Conflict if source_job_id was already approved."""
    try:
        async with db.transaction() as conn:
            cursor = await conn.execute(
                "INSERT INTO questions (title, statement_md, difficulty, topics_json, time_limit_ms, memory_limit_mb, "
                "float_abs, float_rel, created_by, source_job_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (*_fields(data), created_by, source_job_id),
            )
            question_id = cursor.lastrowid
            assert question_id is not None
            await _insert_tests(conn, question_id, data)
    except sqlite3.IntegrityError as e:
        raise Conflict("this draft was already approved") from e
    question = await get(db, question_id)
    assert question is not None
    return question


async def get(db: Database, question_id: int, with_tests: bool = True) -> Question | None:
    """The question, with all its test cases ordered by position if with_tests."""
    async with db.connect() as conn:
        cursor = await conn.execute(f"SELECT {_COLUMNS} FROM questions WHERE id = ?", (question_id,))
        row = await cursor.fetchone()
    if row is None:
        return None
    question = _question(row)
    if with_tests:
        question.test_cases = await get_test_cases(db, question_id)
    return question


async def get_many(db: Database, question_ids: list[int]) -> list[Question]:
    """Questions with these ids (no test cases); missing ids are skipped."""
    if not question_ids:
        return []
    marks = ",".join("?" * len(question_ids))
    async with db.connect() as conn:
        cursor = await conn.execute(f"SELECT {_COLUMNS} FROM questions WHERE id IN ({marks}) ORDER BY id", question_ids)
        return [_question(row) for row in await cursor.fetchall()]


async def get_by_source_job(db: Database, job_id: int) -> Question | None:
    async with db.connect() as conn:
        cursor = await conn.execute(f"SELECT {_COLUMNS} FROM questions WHERE source_job_id = ?", (job_id,))
        row = await cursor.fetchone()
    return _question(row) if row else None


async def list_by_owner(db: Database, teacher_id: int) -> list[Question]:
    """The teacher's questions, newest first, without test cases."""
    async with db.connect() as conn:
        cursor = await conn.execute(
            f"SELECT {_COLUMNS} FROM questions WHERE created_by = ? ORDER BY id DESC", (teacher_id,)
        )
        return [_question(row) for row in await cursor.fetchall()]


async def get_test_cases(db: Database, question_id: int, hidden: bool | None = None) -> list[TestCaseRow]:
    """Test cases ordered by position. hidden=False → visible only, True → hidden only, None → all."""
    sql = "SELECT id, position, is_hidden, stdin, expected_stdout FROM test_cases WHERE question_id = ?"
    params: list = [question_id]
    if hidden is not None:
        sql += " AND is_hidden = ?"
        params.append(int(hidden))
    async with db.connect() as conn:
        cursor = await conn.execute(sql + " ORDER BY position", params)
        rows = await cursor.fetchall()
    return [TestCaseRow(r["id"], r["position"], bool(r["is_hidden"]), r["stdin"], r["expected_stdout"]) for r in rows]


async def count_test_cases(db: Database, question_id: int, hidden: bool | None = None) -> int:
    sql = "SELECT count(*) FROM test_cases WHERE question_id = ?"
    params: list = [question_id]
    if hidden is not None:
        sql += " AND is_hidden = ?"
        params.append(int(hidden))
    async with db.connect() as conn:
        cursor = await conn.execute(sql, params)
        row = await cursor.fetchone()
    return row[0] if row else 0


async def replace(db: Database, question_id: int, data: QuestionIn) -> Question | None:
    """Updates all fields and replaces the test cases. Returns None if not found."""
    async with db.transaction() as conn:
        cursor = await conn.execute(
            "UPDATE questions SET title = ?, statement_md = ?, difficulty = ?, topics_json = ?, time_limit_ms = ?, "
            "memory_limit_mb = ?, float_abs = ?, float_rel = ?, updated_at = ? WHERE id = ?",
            (*_fields(data), now_iso(), question_id),
        )
        if cursor.rowcount == 0:
            return None
        await conn.execute("DELETE FROM test_cases WHERE question_id = ?", (question_id,))
        await _insert_tests(conn, question_id, data)
    return await get(db, question_id)


async def is_used(db: Database, question_id: int) -> bool:
    """True if any assignment uses the question."""
    async with db.connect() as conn:
        cursor = await conn.execute("SELECT 1 FROM assignment_questions WHERE question_id = ? LIMIT 1", (question_id,))
        return await cursor.fetchone() is not None


async def delete(db: Database, question_id: int) -> bool:
    """Returns False if not found; raises Conflict if an assignment uses it."""
    try:
        async with db.transaction() as conn:
            cursor = await conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            return cursor.rowcount > 0
    except sqlite3.IntegrityError as e:
        raise Conflict("question is used by an assignment") from e
