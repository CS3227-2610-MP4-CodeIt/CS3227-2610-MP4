from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite

_APP_DIR = Path(__file__).resolve().parent
# Docker image: /srv/backend-schema.sql; repo checkout: <repo>/specs/backend-schema.sql
_SCHEMA_CANDIDATES = [_APP_DIR.parent / "backend-schema.sql", _APP_DIR.parent.parent / "specs" / "backend-schema.sql"]


def to_iso(dt: datetime) -> str:
    """ISO-8601 UTC with milliseconds, e.g. '2026-10-21T08:30:00.123Z' (the DB format)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def now_iso(offset: timedelta = timedelta()) -> str:
    return to_iso(datetime.now(UTC) + offset)


def schema_path() -> Path:
    for path in _SCHEMA_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("backend-schema.sql not found")


class Database:
    """Opens one short-lived aiosqlite connection per unit of work."""

    def __init__(self, path: str) -> None:
        self.path = path

    @asynccontextmanager
    async def connect(self, foreign_keys: bool = True) -> AsyncIterator[aiosqlite.Connection]:
        conn = await aiosqlite.connect(self.path)
        conn.row_factory = aiosqlite.Row
        try:
            await conn.execute(f"PRAGMA foreign_keys = {'ON' if foreign_keys else 'OFF'}")
            await conn.execute("PRAGMA busy_timeout = 5000")
            yield conn
        finally:
            await conn.close()

    @asynccontextmanager
    async def transaction(self, foreign_keys: bool = True) -> AsyncIterator[aiosqlite.Connection]:
        """Commits on success, rolls back on any exception."""
        async with self.connect(foreign_keys) as conn:
            await conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except BaseException:
                await conn.rollback()
                raise
            await conn.commit()

    async def init_schema(self) -> None:
        """Creates the tables if the database has none (no migrations)."""
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        async with self.connect() as conn:
            await conn.execute("PRAGMA journal_mode = WAL")
            cursor = await conn.execute("SELECT count(*) FROM sqlite_master WHERE type = 'table'")
            row = await cursor.fetchone()
            if row is not None and row[0] == 0:
                await conn.executescript(schema_path().read_text())
                await conn.commit()
