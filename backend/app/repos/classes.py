import sqlite3
from dataclasses import dataclass

import aiosqlite

from app.db import Database
from app.repos import Conflict
from app.repos.users import User

_SELECT = """
SELECT c.id, c.name, c.description, c.created_at,
       (SELECT count(*) FROM class_members m JOIN users u ON u.id = m.user_id
         WHERE m.class_id = c.id AND u.role = 'teacher') AS teacher_count,
       (SELECT count(*) FROM class_members m JOIN users u ON u.id = m.user_id
         WHERE m.class_id = c.id AND u.role = 'student') AS student_count
FROM classes c
"""


@dataclass
class ClassRow:
    id: int
    name: str
    description: str
    created_at: str
    teacher_count: int
    student_count: int


def _class(row: aiosqlite.Row) -> ClassRow:
    return ClassRow(
        row["id"], row["name"], row["description"], row["created_at"], row["teacher_count"], row["student_count"]
    )


async def list_classes(db: Database) -> list[ClassRow]:
    async with db.connect() as conn:
        cursor = await conn.execute(_SELECT + " ORDER BY c.id")
        return [_class(row) for row in await cursor.fetchall()]


async def list_for_user(db: Database, user_id: int) -> list[ClassRow]:
    """Classes the user is a member of."""
    async with db.connect() as conn:
        cursor = await conn.execute(
            _SELECT + " WHERE c.id IN (SELECT class_id FROM class_members WHERE user_id = ?) ORDER BY c.id", (user_id,)
        )
        return [_class(row) for row in await cursor.fetchall()]


async def get(db: Database, class_id: int) -> ClassRow | None:
    async with db.connect() as conn:
        cursor = await conn.execute(_SELECT + " WHERE c.id = ?", (class_id,))
        row = await cursor.fetchone()
    return _class(row) if row else None


async def get_by_name(db: Database, name: str) -> ClassRow | None:
    """Case-insensitive."""
    async with db.connect() as conn:
        cursor = await conn.execute(_SELECT + " WHERE c.name = ?", (name,))
        row = await cursor.fetchone()
    return _class(row) if row else None


async def create(db: Database, name: str, description: str = "") -> ClassRow:
    """Raises Conflict on a duplicate name (case-insensitive)."""
    try:
        async with db.transaction() as conn:
            cursor = await conn.execute("INSERT INTO classes (name, description) VALUES (?, ?)", (name, description))
            class_id = cursor.lastrowid
    except sqlite3.IntegrityError as e:
        raise Conflict("class name already exists") from e
    row = await get(db, class_id)  # type: ignore[arg-type]
    assert row is not None
    return row


async def update(db: Database, class_id: int, *, name: str | None = None, description: str | None = None) -> ClassRow | None:
    """Returns None if not found; raises Conflict on a duplicate name."""
    changes = {k: v for k, v in {"name": name, "description": description}.items() if v is not None}
    if changes:
        try:
            async with db.transaction() as conn:
                sets = ", ".join(f"{k} = ?" for k in changes)
                await conn.execute(f"UPDATE classes SET {sets} WHERE id = ?", (*changes.values(), class_id))
        except sqlite3.IntegrityError as e:
            raise Conflict("class name already exists") from e
    return await get(db, class_id)


async def delete(db: Database, class_id: int) -> bool:
    """Cascades memberships, assignments and their submissions."""
    async with db.transaction() as conn:
        cursor = await conn.execute("DELETE FROM classes WHERE id = ?", (class_id,))
        return cursor.rowcount > 0


async def members(db: Database, class_id: int) -> list[User]:
    """Teachers and students of the class, ordered by id."""
    async with db.connect() as conn:
        cursor = await conn.execute(
            "SELECT u.id, u.username, u.display_name, u.role, u.created_at FROM class_members m "
            "JOIN users u ON u.id = m.user_id WHERE m.class_id = ? ORDER BY u.id",
            (class_id,),
        )
        return [User(r["id"], r["username"], r["display_name"], r["role"], r["created_at"]) for r in await cursor.fetchall()]


async def is_member(db: Database, class_id: int, user_id: int) -> bool:
    async with db.connect() as conn:
        cursor = await conn.execute("SELECT 1 FROM class_members WHERE class_id = ? AND user_id = ?", (class_id, user_id))
        return await cursor.fetchone() is not None


async def add_members(db: Database, class_id: int, user_ids: list[int]) -> None:
    """Adds members; existing members are ignored. The caller must first check that every id is an
    existing teacher/student (users.get_many) and that the class exists."""
    async with db.transaction() as conn:
        await conn.executemany(
            "INSERT OR IGNORE INTO class_members (class_id, user_id) VALUES (?, ?)", [(class_id, u) for u in user_ids]
        )


async def remove_member(db: Database, class_id: int, user_id: int) -> bool:
    async with db.transaction() as conn:
        cursor = await conn.execute("DELETE FROM class_members WHERE class_id = ? AND user_id = ?", (class_id, user_id))
        return cursor.rowcount > 0
