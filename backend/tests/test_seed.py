"""Spec §12.4 demo seed rows and §4 bootstrap admin."""

import httpx
from fastapi import FastAPI

from app.config import Settings
from app.db import Database
from app.main import create_app
from app.repos import classes as classes_repo
from app.repos import users as users_repo


async def _start_and_stop(settings: Settings) -> None:
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        pass


async def test_dev_startup_twice_seeds_once(settings: Settings, mock_http) -> None:
    dev = settings.model_copy(update={"app_env": "dev", "bootstrap_admin_username": None, "bootstrap_admin_password": None})
    await _start_and_stop(dev)
    await _start_and_stop(dev)

    db = Database(dev.database_path)
    users = await users_repo.list_users(db)
    assert len(users) == 23
    assert [u.username for u in users if u.role == "admin"] == ["admin"]
    assert {u.username for u in users if u.role == "teacher"} == {"teacher1", "teacher2"}
    assert len([u for u in users if u.role == "student"]) == 20

    classes = await classes_repo.list_classes(db)
    assert [(c.name, c.teacher_count, c.student_count) for c in classes] == [
        ("Demo Class A", 1, 10),
        ("Demo Class B", 1, 10),
    ]
    class_a = [m.username for m in await classes_repo.members(db, classes[0].id)]
    assert "teacher1" in class_a and "student01" in class_a and "student11" not in class_a


async def test_dev_seed_skips_admin_when_bootstrap_admin_exists(settings: Settings, mock_http) -> None:
    dev = settings.model_copy(update={"app_env": "dev"})
    app = create_app(dev)
    async with app.router.lifespan_context(app):
        db = app.state.ctx.db
        admins = await users_repo.list_users(db, "admin")
        assert [a.username for a in admins] == [settings.bootstrap_admin_username]
        assert len(await users_repo.list_users(db)) == 23
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/auth/login", json={"username": "student07", "password": "demo1234"})
            assert response.status_code == 200
            assert (await client.get("/docs")).status_code == 200  # docs on in dev


async def test_prod_has_no_demo_accounts(app: FastAPI, db: Database) -> None:
    users = await users_repo.list_users(db)
    assert [(u.username, u.role) for u in users] == [("rootadmin", "admin")]
    assert await classes_repo.list_classes(db) == []
