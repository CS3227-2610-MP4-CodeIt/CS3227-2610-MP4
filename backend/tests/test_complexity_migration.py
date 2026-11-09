import asyncio

from app.db import Database, schema_path


async def test_existing_jobs_schema_is_upgraded_without_losing_rows(tmp_path):
    db = Database(str(tmp_path / "old.db"))
    old_schema = schema_path().read_text().replace("'hint', 'complexity',", "'hint',")
    async with db.connect() as conn:
        await conn.execute("PRAGMA journal_mode = WAL")
        await conn.executescript(old_schema)
        await conn.execute(
            "INSERT INTO users (username, password_hash, display_name, role) VALUES ('student', 'x', 'S', 'student')"
        )
        await conn.execute(
            "INSERT INTO jobs (id, user_id, kind, target_key, status, input_json, result_json, finished_at) VALUES (42, 1, 'hint', 'a1:q1', 'success', ?, ?, ?)",
            ('{"code":"snapshot"}', '{"hint":"ok"}', "2026-01-01T00:00:00Z"),
        )
        await conn.commit()
    await asyncio.gather(db.init_schema(), db.init_schema())
    async with db.connect() as conn:
        await conn.execute(
            "INSERT INTO jobs (user_id, kind, target_key, input_json) VALUES (1, 'complexity', 'a1:q1:s1', '{}')"
        )
        rows = await (
            await conn.execute(
                "SELECT id, kind, input_json, result_json, finished_at FROM jobs ORDER BY id"
            )
        ).fetchall()
        assert tuple(rows[0]) == (
            42,
            "hint",
            '{"code":"snapshot"}',
            '{"hint":"ok"}',
            "2026-01-01T00:00:00Z",
        )
        assert rows[1][1] == "complexity"
        indexes = await (await conn.execute("PRAGMA index_list(jobs)")).fetchall()
        assert {row[1] for row in indexes} >= {"jobs_one_in_process", "jobs_latest"}
        assert await (await conn.execute("PRAGMA foreign_key_check")).fetchall() == []
