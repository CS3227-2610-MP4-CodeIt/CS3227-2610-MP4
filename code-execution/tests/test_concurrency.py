import asyncio
import os
import time

import httpx
import pytest

from app.config import Settings
from app.main import create_app
from tests.conftest import AUTH, TOKEN, job
from tests.test_security import processes_matching


async def test_jobs_run_concurrently(execute):
    start = time.monotonic()
    results = await asyncio.gather(*(execute(job("import time; time.sleep(1)", time_limit_ms=2000)) for _ in range(20)))
    assert all(r["verdict"] == "ACCEPTED" for r in results)
    assert time.monotonic() - start < 3


async def test_health_responsive_during_job(client):
    task = asyncio.create_task(client.post("/v1/execute", json=job("while True: pass", time_limit_ms=2000), headers=AUTH))
    await asyncio.sleep(0.3)
    start = time.monotonic()
    r = await client.get("/health")
    assert time.monotonic() - start < 0.1
    assert r.json()["available_slots"] == 99
    assert (await task).json()["verdict"] == "TIME_LIMIT_EXCEEDED"


async def test_queue_timeout_returns_503(tmp_path):
    app = create_app(Settings(executor_token=TOKEN, work_root=str(tmp_path), max_concurrent_jobs=2, queue_timeout_s=1))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", timeout=30) as c:
            body = job("import time; time.sleep(3)", time_limit_ms=5000)
            responses = await asyncio.gather(*(c.post("/v1/execute", json=body, headers=AUTH) for _ in range(3)))
    codes = sorted(r.status_code for r in responses)
    assert codes == [200, 200, 503]
    busy = next(r for r in responses if r.status_code == 503)
    assert "retry-after" in busy.headers


async def test_cancel_kills_child_and_cleans_up(client, work_root):
    code = "import os\nos.execv('/bin/sleep', ['sleep', '987655'])"
    task = asyncio.create_task(client.post("/v1/execute", json=job(code, time_limit_ms=10_000), headers=AUTH))
    await asyncio.sleep(0.5)
    assert processes_matching("sleep 987655") != []
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await asyncio.sleep(0.1)
    assert processes_matching("sleep 987655") == []
    assert os.listdir(work_root) == []
