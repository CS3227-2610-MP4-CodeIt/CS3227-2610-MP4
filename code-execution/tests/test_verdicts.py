import time

import pytest

from tests.conftest import job


async def test_accepted(execute):
    r = await execute(job("print(int(input())*2)", [("3\n", "6\n"), ("10\n", "20\n")]))
    assert r["verdict"] == "ACCEPTED"
    assert r["passed"] == 2 and r["total"] == 2
    assert r["failed_test_index"] is None and r["error_message"] is None
    assert [res["status"] for res in r["results"]] == ["ACCEPTED", "ACCEPTED"]
    assert "stdout_preview" not in r["results"][0]


async def test_trailing_whitespace(execute):
    r = await execute(job('print("6  \\n\\n")', [("", "6")]))
    assert r["verdict"] == "ACCEPTED"


async def test_wrong_answer(execute):
    r = await execute(job("print(0)", [("", "0"), ("", "1")]))
    assert r["verdict"] == "WRONG_ANSWER"
    assert r["failed_test_index"] == 1
    assert r["error_message"] == "Line 1 differs"
    assert r["results"][1]["stdout_preview"] == "0\n"


async def test_stops_at_first_failure(execute):
    r = await execute(job("print(input())", [("a", "a"), ("b", "x"), ("c", "c")]))
    assert r["verdict"] == "WRONG_ANSWER"
    assert len(r["results"]) == 2
    assert r["passed"] == 1 and r["total"] == 3


async def test_time_limit_is_per_test(execute):
    r = await execute(job("import time; time.sleep(0.8)", [("", "")] * 5, time_limit_ms=1000))
    assert r["verdict"] == "ACCEPTED"
    assert r["max_time_ms"] < 1000


async def test_memory_limit_is_per_test(execute):
    code = "a = bytearray(40 * 1024 * 1024)\nprint(len(a))"
    r = await execute(job(code, [("", str(40 * 1024 * 1024))] * 3, memory_limit_mb=64))
    assert r["verdict"] == "ACCEPTED"


async def test_syntax_error(execute):
    r = await execute(job("print("))
    assert r["verdict"] == "RUNTIME_ERROR"
    assert "SyntaxError" in r["error_message"]
    assert "solution.py" in r["error_message"]


async def test_exception_is_sanitised(execute, work_root):
    r = await execute(job("1/0"))
    message = r["error_message"]
    assert r["verdict"] == "RUNTIME_ERROR"
    assert message.rstrip().splitlines()[-1].startswith("ZeroDivisionError")
    assert "harness" not in message
    assert str(work_root) not in message


async def test_sys_exit_nonzero(execute):
    r = await execute(job("import sys; sys.exit(3)"))
    assert r["verdict"] == "RUNTIME_ERROR"


async def test_sys_exit_zero_mid_way(execute):
    r = await execute(job("import sys\nprint(6)\nsys.exit(0)\nprint(7)", [("", "6")]))
    assert r["verdict"] == "ACCEPTED"


async def test_cpu_loop(execute):
    start = time.monotonic()
    r = await execute(job("while True: pass", time_limit_ms=1000))
    assert r["verdict"] == "TIME_LIMIT_EXCEEDED"
    assert time.monotonic() - start < 1000 / 1000 + 0.5 + 1


async def test_sleep(execute):
    r = await execute(job("import time; time.sleep(60)", time_limit_ms=500))
    assert r["verdict"] == "TIME_LIMIT_EXCEEDED"


async def test_memory_limit(execute):
    r = await execute(job("a = [0] * 10**9", memory_limit_mb=64))
    assert r["verdict"] == "MEMORY_LIMIT_EXCEEDED"


async def test_recursion(execute):
    r = await execute(job("def f(n): return f(n + 1)\nf(0)"))
    assert r["verdict"] == "RUNTIME_ERROR"
    assert "RecursionError" in r["error_message"]


async def test_does_not_read_stdin(execute):
    r = await execute(job("print(6)", [("1 " * 500_000, "6")]))
    assert r["verdict"] == "ACCEPTED"


TOL = {"abs": 1e-6, "rel": 1e-6}


@pytest.mark.parametrize(
    ("actual", "expected", "tolerance", "verdict"),
    [
        ("print(1/3)", "0.333333", TOL, "ACCEPTED"),
        ("print(1/3)", "0.333333", None, "WRONG_ANSWER"),
        ("print('1.0000000001e18')", "1e18", TOL, "ACCEPTED"),
        ("print('1e-9')", "0", {"abs": 1e-6, "rel": 0}, "ACCEPTED"),
        ("print('3.0')", "3", TOL, "ACCEPTED"),
        ("print('YES 2.5000001')", "YES 2.5", TOL, "ACCEPTED"),
        ("print('NO 2.5')", "YES 2.5", TOL, "WRONG_ANSWER"),
        ("print('nan')", "nan", TOL, "ACCEPTED"),
        ("print('nan')", "0.5", TOL, "WRONG_ANSWER"),
        ("print('1 2')", "1 2 3", TOL, "WRONG_ANSWER"),
        ("print('1\\n2')", "1 2", TOL, "WRONG_ANSWER"),
        ("print('0.1000001\\n0.2\\n0.2999999')", "0.1\n0.2\n0.3", TOL, "ACCEPTED"),
    ],
)
async def test_float_tolerance(execute, actual, expected, tolerance, verdict):
    r = await execute(job(actual, [("", expected)], float_tolerance=tolerance))
    assert r["verdict"] == verdict, r["error_message"]


async def test_float_outside_tolerance_message(execute):
    r = await execute(job("print('0.334')", [("", "0.333333")], float_tolerance=TOL))
    assert r["verdict"] == "WRONG_ANSWER"
    assert r["error_message"].startswith("Line 1, token 1: expected 0.333333, got 0.334")
    assert "6.7e-04" in r["error_message"]
