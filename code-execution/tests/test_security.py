import os
import subprocess

from tests.conftest import TOKEN, job


def processes_matching(marker: str) -> list[str]:
    out = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if marker in line and "ps -eo" not in line]


async def test_output_flood(execute):
    r = await execute(job('while True: print("x" * 10**6)', time_limit_ms=5000))
    assert r["verdict"] == "RUNTIME_ERROR"
    assert r["error_message"] == "Output limit exceeded"


async def test_env_has_no_secrets(execute, monkeypatch):
    monkeypatch.setenv("EXECUTOR_TOKEN", TOKEN)
    r = await execute(job("import os; print(os.environ)", [("", "x")]))
    assert TOKEN not in r["results"][0]["stdout_preview"]
    assert "EXECUTOR_TOKEN" not in r["results"][0]["stdout_preview"]


async def test_forked_children_are_killed(execute):
    # Bounded fork loop (a real fork bomb would hurt the dev machine; the container pids limit covers that).
    code = (
        "import os\n"
        "for _ in range(20):\n"
        "    if os.fork() == 0:\n"
        "        os.execv('/bin/sleep', ['sleep', '987653'])\n"
        "print('done')\n"
    )
    r = await execute(job(code, [("", "done")]))
    assert r["verdict"] == "ACCEPTED"
    assert processes_matching("sleep 987653") == []


async def test_background_process_is_killed(execute):
    code = "import subprocess\nsubprocess.Popen(['sleep', '987654'])\nprint('ok')"
    r = await execute(job(code, [("", "ok")]))
    assert r["verdict"] == "ACCEPTED"
    assert processes_matching("sleep 987654") == []


async def test_large_file_write_fails(execute):
    r = await execute(job("open('big', 'wb').write(b'x' * 100 * 1024 * 1024)", memory_limit_mb=256))
    assert r["verdict"] == "RUNTIME_ERROR"


async def test_stdlib_not_shadowed(execute):
    # The harness already imports json, so shadow a module it doesn't load.
    code = (
        "open('statistics.py', 'w').write('raise SystemExit(5)')\n"
        "import statistics\n"
        "print(statistics.mean([1, 3]))\n"
    )
    r = await execute(job(code, [("", "2")]))
    assert r["verdict"] == "ACCEPTED", r["error_message"]


async def test_workdir_removed_after_job(execute, work_root):
    await execute(job("open('f.txt', 'w').write('x')"))
    assert os.listdir(work_root) == []
