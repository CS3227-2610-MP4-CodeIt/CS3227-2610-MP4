from dataclasses import dataclass, field
from datetime import datetime

import aiosqlite

from app.db import Database, now_iso, to_iso
from app.repos import Conflict

_SELECT = """
SELECT a.id, a.class_id, c.name AS class_name, a.created_by, a.title, a.description_md, a.due_at,
       a.created_at, a.updated_at
FROM assignments a JOIN classes c ON c.id = a.class_id
"""

_UNSET = object()


@dataclass
class AssignmentQuestion:
    id: int  # question id
    position: int
    title: str
    difficulty: str


@dataclass
class Assignment:
    id: int
    class_id: int
    class_name: str
    created_by: int | None
    title: str
    description_md: str
    due_at: str | None  # ISO UTC or None
    created_at: str
    updated_at: str
    questions: list[AssignmentQuestion] = field(default_factory=list)  # ordered by position

    def is_past_due(self) -> bool:
        return self.due_at is not None and now_iso() > self.due_at

    def has_question(self, question_id: int) -> bool:
        return any(q.id == question_id for q in self.questions)


def _assignment(row: aiosqlite.Row) -> Assignment:
    return Assignment(
        row["id"], row["class_id"], row["class_name"], row["created_by"], row["title"], row["description_md"],
        row["due_at"], row["created_at"], row["updated_at"],
    )


async def _with_questions(conn: aiosqlite.Connection, assignments: list[Assignment]) -> list[Assignment]:
    if not assignments:
        return assignments
    by_id = {a.id: a for a in assignments}
    marks = ",".join("?" * len(by_id))
    cursor = await conn.execute(
        "SELECT aq.assignment_id, q.id, aq.position, q.title, q.difficulty FROM assignment_questions aq "
        f"JOIN questions q ON q.id = aq.question_id WHERE aq.assignment_id IN ({marks}) "
        "ORDER BY aq.assignment_id, aq.position",
        list(by_id),
    )
    for r in await cursor.fetchall():
        by_id[r["assignment_id"]].questions.append(AssignmentQuestion(r["id"], r["position"], r["title"], r["difficulty"]))
    return assignments


async def _query(db: Database, where: str, params: tuple) -> list[Assignment]:
    async with db.connect() as conn:
        cursor = await conn.execute(f"{_SELECT} {where}", params)
        assignments = [_assignment(row) for row in await cursor.fetchall()]
        return await _with_questions(conn, assignments)


async def get(db: Database, assignment_id: int) -> Assignment | None:
    """The assignment with its questions (any class)."""
    found = await _query(db, "WHERE a.id = ?", (assignment_id,))
    return found[0] if found else None


async def get_for_member(db: Database, assignment_id: int, user_id: int) -> Assignment | None:
    """The assignment only if user_id is a member (teacher or student) of its class."""
    found = await _query(
        db,
        "WHERE a.id = ? AND EXISTS (SELECT 1 FROM class_members m WHERE m.class_id = a.class_id AND m.user_id = ?)",
        (assignment_id, user_id),
    )
    return found[0] if found else None


async def list_for_member(db: Database, user_id: int, class_id: int | None = None) -> list[Assignment]:
    """Assignments of every class the user belongs to (optionally one class), newest first."""
    where = "WHERE a.class_id IN (SELECT class_id FROM class_members WHERE user_id = ?)"
    params: tuple = (user_id,)
    if class_id is not None:
        where += " AND a.class_id = ?"
        params += (class_id,)
    return await _query(db, where + " ORDER BY a.id DESC", params)


async def list_for_class(db: Database, class_id: int) -> list[Assignment]:
    return await _query(db, "WHERE a.class_id = ? ORDER BY a.id DESC", (class_id,))


async def create(
    db: Database,
    class_id: int,
    created_by: int,
    title: str,
    description_md: str,
    due_at: datetime | None,
    question_ids: list[int],
) -> Assignment:
    """The caller checks membership, question ownership and 1-3 distinct ids."""
    async with db.transaction() as conn:
        cursor = await conn.execute(
            "INSERT INTO assignments (class_id, created_by, title, description_md, due_at) VALUES (?, ?, ?, ?, ?)",
            (class_id, created_by, title, description_md, to_iso(due_at) if due_at else None),
        )
        assignment_id = cursor.lastrowid
        await conn.executemany(
            "INSERT INTO assignment_questions (assignment_id, question_id, position) VALUES (?, ?, ?)",
            [(assignment_id, q, i) for i, q in enumerate(question_ids, 1)],
        )
    found = await get(db, assignment_id)  # type: ignore[arg-type]
    assert found is not None
    return found


async def has_submissions(db: Database, assignment_id: int, question_id: int) -> bool:
    async with db.connect() as conn:
        cursor = await conn.execute(
            "SELECT 1 FROM submissions WHERE assignment_id = ? AND question_id = ? LIMIT 1", (assignment_id, question_id)
        )
        return await cursor.fetchone() is not None


async def update(
    db: Database,
    assignment_id: int,
    *,
    title: str | None = None,
    description_md: str | None = None,
    due_at: datetime | None | object = _UNSET,
    question_ids: list[int] | None = None,
) -> Assignment | None:
    """Updates the given fields (pass due_at=None to clear the deadline; omit it to keep it).
    question_ids replaces the question list/order; raises Conflict if a removed question has
    submissions. Returns None if not found. The caller checks question ownership."""
    current = await get(db, assignment_id)
    if current is None:
        return None
    if question_ids is not None:
        for q in current.questions:
            if q.id not in question_ids and await has_submissions(db, assignment_id, q.id):
                raise Conflict("a question with submissions cannot be removed from the assignment")
    changes: dict[str, object] = {k: v for k, v in {"title": title, "description_md": description_md}.items() if v is not None}
    if due_at is not _UNSET:
        changes["due_at"] = to_iso(due_at) if isinstance(due_at, datetime) else None
    # foreign_keys OFF: re-inserting the question rows must not cascade-delete kept submissions.
    async with db.transaction(foreign_keys=False) as conn:
        sets = "".join(f"{k} = ?, " for k in changes)
        await conn.execute(
            f"UPDATE assignments SET {sets}updated_at = ? WHERE id = ?", (*changes.values(), now_iso(), assignment_id)
        )
        if question_ids is not None:
            await conn.execute("DELETE FROM assignment_questions WHERE assignment_id = ?", (assignment_id,))
            await conn.executemany(
                "INSERT INTO assignment_questions (assignment_id, question_id, position) VALUES (?, ?, ?)",
                [(assignment_id, q, i) for i, q in enumerate(question_ids, 1)],
            )
    return await get(db, assignment_id)


async def delete(db: Database, assignment_id: int) -> bool:
    """Cascades its submissions."""
    async with db.transaction() as conn:
        cursor = await conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        return cursor.rowcount > 0
