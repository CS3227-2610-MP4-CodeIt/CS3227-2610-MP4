"""Spec §12.3 (generic parts) and §4 login / sessions."""

from datetime import timedelta

import httpx
from fastapi import Depends, FastAPI

from app.auth import require_admin, require_teacher, token_hash
from app.db import Database, now_iso
from app.repos import jobs as jobs_repo
from app.repos import users as users_repo
from tests.conftest import BOOTSTRAP_ADMIN, TestUser


async def test_health_needs_no_auth(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_login_me_logout(client: httpx.AsyncClient, teacher: TestUser) -> None:
    response = await client.post("/api/auth/login", json={"username": teacher.user.username, "password": teacher.password})
    assert response.status_code == 200
    body = response.json()
    assert body["user"] == {
        "id": teacher.id,
        "username": teacher.user.username,
        "display_name": teacher.user.display_name,
        "role": "teacher",
    }
    headers = {"Authorization": f"Bearer {body['token']}"}

    me = await client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200 and me.json()["id"] == teacher.id

    assert (await client.post("/api/auth/logout", headers=headers)).status_code == 204
    assert (await client.get("/api/auth/me", headers=headers)).status_code == 401
    # other sessions of the same user are untouched
    assert (await client.get("/api/auth/me", headers=teacher.headers)).status_code == 200


async def test_login_is_case_insensitive_and_bootstrap_admin_exists(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"username": BOOTSTRAP_ADMIN[0].upper(), "password": BOOTSTRAP_ADMIN[1]}
    )
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"


async def test_login_failures_look_the_same(client: httpx.AsyncClient, student: TestUser) -> None:
    wrong = await client.post("/api/auth/login", json={"username": student.user.username, "password": "wrong-password"})
    unknown = await client.post("/api/auth/login", json={"username": "nobody", "password": "wrong-password"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "invalid credentials"}


async def test_token_is_stored_hashed(db: Database, student: TestUser) -> None:
    assert await users_repo.get_session_user(db, token_hash(student.token)) is not None
    assert await users_repo.get_session_user(db, student.token) is None


async def test_no_bad_or_expired_token(client: httpx.AsyncClient, db: Database, student: TestUser) -> None:
    assert (await client.get("/api/auth/me")).status_code == 401
    assert (await client.get("/api/auth/me", headers={"Authorization": "Bearer nope"})).status_code == 401
    assert (await client.get("/api/auth/me", headers={"Authorization": "Basic abc"})).status_code == 401

    await users_repo.create_session(db, token_hash("expired-token"), student.id, now_iso(timedelta(seconds=-1)))
    expired = await client.get("/api/auth/me", headers={"Authorization": "Bearer expired-token"})
    assert expired.status_code == 401


async def test_deleted_users_token(client: httpx.AsyncClient, db: Database, student: TestUser) -> None:
    assert await users_repo.delete(db, student.id)
    assert (await client.get("/api/auth/me", headers=student.headers)).status_code == 401


async def test_password_change_ends_sessions(client: httpx.AsyncClient, db: Database, student: TestUser) -> None:
    await users_repo.update(db, student.id, password_hash="new-hash")
    assert (await client.get("/api/auth/me", headers=student.headers)).status_code == 401


async def test_wrong_role_is_403(app: FastAPI, client: httpx.AsyncClient, student: TestUser, admin: TestUser) -> None:
    async def probe() -> dict:
        return {"ok": True}

    app.add_api_route("/api/admin/_probe", probe, dependencies=[Depends(require_admin)])
    app.add_api_route("/api/teacher/_probe", probe, dependencies=[Depends(require_teacher)])

    assert (await client.get("/api/admin/_probe", headers=student.headers)).status_code == 403
    assert (await client.get("/api/teacher/_probe", headers=student.headers)).status_code == 403
    assert (await client.get("/api/teacher/_probe", headers=admin.headers)).status_code == 403
    assert (await client.get("/api/admin/_probe", headers=admin.headers)).status_code == 200
    assert (await client.get("/api/admin/_probe")).status_code == 401


async def test_other_users_job_is_404(client: httpx.AsyncClient, db: Database, student: TestUser, make_user) -> None:
    other = await make_user("student")
    job = await jobs_repo.insert_in_process(db, other.id, "hint", "a1:q1", {"code": "secret"})

    assert (await client.get(f"/api/jobs/{job.id}", headers=student.headers)).status_code == 404
    assert (await client.get("/api/jobs/999999", headers=student.headers)).status_code == 404
    own = await client.get(f"/api/jobs/{job.id}", headers=other.headers)
    assert own.status_code == 200
    assert own.json()["status"] == "in_process"
    assert "input" not in own.json()


async def test_cors_is_open(client: httpx.AsyncClient) -> None:
    response = await client.options(
        "/api/auth/me",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET",
                 "Access-Control-Request-Headers": "authorization"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


async def test_prod_disables_docs(client: httpx.AsyncClient) -> None:
    assert (await client.get("/docs")).status_code == 404
    assert (await client.get("/openapi.json")).status_code == 404
