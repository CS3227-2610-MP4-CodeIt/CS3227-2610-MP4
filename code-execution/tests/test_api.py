import pytest

from app.main import MAX_BODY_BYTES
from tests.conftest import AUTH, job


async def test_health_needs_no_auth(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "available_slots": 100, "max_slots": 100}


@pytest.mark.parametrize("headers", [{}, {"X-Internal-Token": "wrong"}])
async def test_bad_token(client, headers):
    r = await client.post("/v1/execute", json=job("print(1)"), headers=headers)
    assert r.status_code == 401


async def test_body_too_large(client):
    r = await client.post(
        "/v1/execute", content=b"x" * (MAX_BODY_BYTES + 1), headers={**AUTH, "Content-Type": "application/json"}
    )
    assert r.status_code == 413


@pytest.mark.parametrize(
    "body",
    [
        job(""),
        job("x" * (64 * 1024 + 1)),
        job("print(1)\x00"),
        job("print(1)", [("", "")] * 101),
        job("print(1)", []),
        job("print(1)", time_limit_ms=99),
        job("print(1)", time_limit_ms=10_001),
        job("print(1)", memory_limit_mb=15),
        job("print(1)", memory_limit_mb=1025),
        job("print(1)", [("x" * (1024 * 1024 + 1), "")]),
        job("print(1)", float_tolerance={"abs": 0, "rel": 0}),
        job("print(1)", float_tolerance={"abs": -1e-6}),
        job("print(1)", float_tolerance={"rel": 1.5}),
    ],
)
async def test_validation(client, body):
    r = await client.post("/v1/execute", json=body, headers=AUTH)
    assert r.status_code == 422


async def test_cors_is_open(client):
    r = await client.options(
        "/v1/execute",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert r.headers["access-control-allow-origin"] in ("*", "http://localhost:5173")
