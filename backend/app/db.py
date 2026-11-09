from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite

# backend/backend-schema.sql (/srv/backend-schema.sql in the Docker image)
_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "backend-schema.sql"


def to_iso(dt: datetime) -> str:
    """ISO-8601 UTC with milliseconds, e.g. '2026-10-21T08:30:00.123Z' (the DB format)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def now_iso(offset: timedelta = timedelta()) -> str:
    return to_iso(datetime.now(UTC) + offset)


def schema_path() -> Path:
    if not _SCHEMA_PATH.exists():
        raise FileNotFoundError("backend-schema.sql not found")
    return _SCHEMA_PATH


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
        """Create the schema or upgrade the jobs kind constraint."""
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        async with self.connect() as conn:
            await conn.execute("PRAGMA journal_mode = WAL")
            cursor = await conn.execute("SELECT count(*) FROM sqlite_master WHERE type = 'table'")
            row = await cursor.fetchone()
            if row is not None and row[0] == 0:
                await conn.executescript(schema_path().read_text())
                await conn.commit()

        async with self.connect(foreign_keys=False) as conn:
            # Serialize the decision with the rebuild so a second initializer sees
            # the schema committed by the first, rather than rebuilding it again.
            await conn.execute("BEGIN IMMEDIATE")
            try:
                cursor = await conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name='jobs'"
                )
                row = await cursor.fetchone()
                if row and "'complexity'" not in row[0]:
                    create = row[0].replace("CREATE TABLE jobs", "CREATE TABLE jobs_new", 1)
                    create = create.replace("'hint',", "'hint', 'complexity',", 1)
                    await conn.execute(create)
                    await conn.execute("INSERT INTO jobs_new SELECT * FROM jobs")
                    await conn.execute("DROP TABLE jobs")
                    await conn.execute("ALTER TABLE jobs_new RENAME TO jobs")
                    await conn.execute(
                        "CREATE UNIQUE INDEX jobs_one_in_process ON jobs(user_id, kind, target_key) WHERE status = 'in_process'"
                    )
                    await conn.execute(
                        "CREATE INDEX jobs_latest ON jobs(user_id, kind, target_key, id DESC)"
                    )
                await conn.commit()
            except BaseException:
                await conn.rollback()
                raise
