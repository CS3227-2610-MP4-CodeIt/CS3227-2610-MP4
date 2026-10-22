import sqlite3
from dataclasses import dataclass

import aiosqlite

from app.db import Database, now_iso
from app.repos import Conflict

_COLUMNS = "id, username, display_name, role, created_at"


@dataclass
class User:
    id: int
    username: str
    display_name: str
    role: str  # admin / teacher / student
    created_at: str


def _user(row: aiosqlite.Row) -> User:
    return User(row["id"], row["username"], row["display_name"], row["role"], row["created_at"])


async def get(db: Database, user_id: int) -> User | None:
    async with db.connect() as conn:
        cursor = await conn.execute(f"SELECT {_COLUMNS} FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
    return _user(row) if row else None


async def get_many(db: Database, user_ids: list[int]) -> list[User]:
    """Users with these ids (missing ids are skipped), ordered by id."""
    if not user_ids:
        return []
    marks = ",".join("?" * len(user_ids))
    async with db.connect() as conn:
        cursor = await conn.execute(f"SELECT {_COLUMNS} FROM users WHERE id IN ({marks}) ORDER BY id", user_ids)
        return [_user(row) for row in await cursor.fetchall()]


async def get_with_password_hash(db: Database, username: str) -> tuple[User, str] | None:
    """Case-insensitive username lookup, for login."""
    async with db.connect() as conn:
        cursor = await conn.execute(f"SELECT {_COLUMNS}, password_hash FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
    return (_user(row), row["password_hash"]) if row else None


async def list_users(db: Database, role: str | None = None) -> list[User]:
    async with db.connect() as conn:
        if role is None:
            cursor = await conn.execute(f"SELECT {_COLUMNS} FROM users ORDER BY id")
        else:
            cursor = await conn.execute(f"SELECT {_COLUMNS} FROM users WHERE role = ? ORDER BY id", (role,))
        return [_user(row) for row in await cursor.fetchall()]


async def count_admins(db: Database) -> int:
    async with db.connect() as conn:
        cursor = await conn.execute("SELECT count(*) FROM users WHERE role = 'admin'")
        row = await cursor.fetchone()
    return row[0] if row else 0


async def create(db: Database, username: str, display_name: str, password_hash: str, role: str) -> User:
    """Raises Conflict if the username is taken (case-insensitive)."""
    try:
        async with db.transaction() as conn:
            cursor = await conn.execute(
                "INSERT INTO users (username, display_name, password_hash, role) VALUES (?, ?, ?, ?)",
                (username, display_name, password_hash, role),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError as e:
        raise Conflict("username already exists") from e
    user = await get(db, user_id)  # type: ignore[arg-type]
    assert user is not None
    return user


async def update(
    db: Database,
    user_id: int,
    *,
    username: str | None = None,
    display_name: str | None = None,
    password_hash: str | None = None,
) -> User | None:
    """Updates the given fields. A new password also deletes the user's sessions.
    Returns None if the user does not exist; raises Conflict on a duplicate username."""
    fields = {"username": username, "display_name": display_name, "password_hash": password_hash}
    changes = {k: v for k, v in fields.items() if v is not None}
    try:
        async with db.transaction() as conn:
            if changes:
                sets = ", ".join(f"{k} = ?" for k in changes)
                await conn.execute(
                    f"UPDATE users SET {sets}, updated_at = ? WHERE id = ?", (*changes.values(), now_iso(), user_id)
                )
            if password_hash is not None:
                await conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    except sqlite3.IntegrityError as e:
        raise Conflict("username already exists") from e
    return await get(db, user_id)


async def delete(db: Database, user_id: int) -> bool:
    """Cascades sessions, memberships, submissions, jobs. Returns False if not found."""
    async with db.transaction() as conn:
        cursor = await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0


# --- sessions ---------------------------------------------------------------


async def create_session(db: Database, token_hash: str, user_id: int, expires_at: str) -> None:
    async with db.transaction() as conn:
        await conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)", (token_hash, user_id, expires_at)
        )


async def get_session_user(db: Database, token_hash: str) -> User | None:
    """The user of a non-expired session, or None."""
    async with db.connect() as conn:
        cursor = await conn.execute(
            f"SELECT {', '.join('u.' + c.strip() for c in _COLUMNS.split(','))} FROM sessions s "
            "JOIN users u ON u.id = s.user_id WHERE s.token_hash = ? AND s.expires_at > ?",
            (token_hash, now_iso()),
        )
        row = await cursor.fetchone()
    return _user(row) if row else None


async def delete_session(db: Database, token_hash: str) -> None:
    async with db.transaction() as conn:
        await conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))


async def delete_sessions_of_user(db: Database, user_id: int) -> None:
    async with db.transaction() as conn:
        await conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
