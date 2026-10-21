import asyncio
import json
import os
import signal
import sys
import time
from asyncio.subprocess import PIPE, Process
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings

HARNESS_PATH = str(Path(__file__).with_name("harness.py"))
STDERR_CAP = 64 * 1024
MIN_STDOUT_CAP = 64 * 1024
REPORT_CAP = 64 * 1024
CHILD_ENV = {"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}


@dataclass
class RunResult:
    exit_code: int | None  # None if killed by signal
    signal: int | None
    timed_out: bool
    output_limit_exceeded: bool
    time_ms: int
    peak_rss_kb: int | None
    report: dict | None
    stdout: bytes
    stderr: bytes


def _kill_group(proc: Process) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def _read_report(fd: int) -> dict | None:
    data = bytearray()
    try:
        while len(data) < REPORT_CAP and (chunk := os.read(fd, 4096)):
            data.extend(chunk)
    except BlockingIOError:
        pass
    try:
        report = json.loads(data)
    except ValueError:
        return None
    return report if isinstance(report, dict) else None


async def run_test(
    workdir: str,
    stdin: str,
    expected_stdout: str,
    time_limit_ms: int,
    memory_limit_mb: int,
    settings: Settings,
) -> RunResult:
    stdout_cap = min(max(len(expected_stdout.encode()) * 2, MIN_STDOUT_CAP), settings.max_stdout_bytes)
    stdout, stderr = bytearray(), bytearray()
    output_limit_exceeded = False
    timed_out = False

    report_r, report_w = os.pipe()
    os.set_blocking(report_r, False)
    start = time.monotonic()
    end = start
    try:
        # -P (no script dir on sys.path), -s (no user site), -B (no .pyc): the parts of -I we need.
        # -I itself would also ignore PYTHONHASHSEED, and the env is already a fresh minimal dict.
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-P", "-s", "-B", "-X", "utf8", HARNESS_PATH,
            "solution.py", str(time_limit_ms), str(memory_limit_mb),
            str(settings.as_overhead_mb), str(settings.fsize_limit_bytes), str(report_w),
            stdin=PIPE, stdout=PIPE, stderr=PIPE,
            pass_fds=(report_w,),
            cwd=workdir,
            env=CHILD_ENV,
            start_new_session=True,
        )
    finally:
        os.close(report_w)

    async def feed_stdin() -> None:
        assert proc.stdin is not None
        try:
            proc.stdin.write(stdin.encode())
            await proc.stdin.drain()
            proc.stdin.close()
            await proc.stdin.wait_closed()
        except (BrokenPipeError, ConnectionResetError):
            pass

    async def read_capped(stream: asyncio.StreamReader, buf: bytearray, cap: int) -> None:
        nonlocal output_limit_exceeded
        while chunk := await stream.read(65536):
            if len(buf) + len(chunk) > cap:
                buf.extend(chunk[: cap - len(buf)])
                output_limit_exceeded = True
                _kill_group(proc)
                return
            buf.extend(chunk)

    async def wait_exit() -> None:
        # proc.wait() also waits for the pipes to close, which leftover descendants keep open,
        # so watch the process itself through a pidfd.
        nonlocal end
        try:
            pidfd = os.pidfd_open(proc.pid)
        except ProcessLookupError:  # already exited and reaped
            pidfd = None
        if pidfd is not None:
            loop = asyncio.get_running_loop()
            exited = loop.create_future()
            loop.add_reader(pidfd, lambda: exited.done() or exited.set_result(None))
            try:
                await exited
            finally:
                loop.remove_reader(pidfd)
                os.close(pidfd)
        end = time.monotonic()
        # Kill anything the program left running in its group so the pipes reach EOF.
        _kill_group(proc)

    try:
        assert proc.stdout is not None and proc.stderr is not None
        async with asyncio.timeout(time_limit_ms / 1000 + settings.wall_grace_s):
            await asyncio.gather(
                feed_stdin(),
                read_capped(proc.stdout, stdout, stdout_cap),
                read_capped(proc.stderr, stderr, STDERR_CAP),
                wait_exit(),
            )
    except TimeoutError:
        timed_out = True
        end = time.monotonic()
    finally:
        # Also runs on CancelledError (client disconnected); the error is re-raised afterwards.
        _kill_group(proc)
        await proc.wait()
        report = _read_report(report_r)
        os.close(report_r)

    returncode = proc.returncode
    assert returncode is not None
    peak_rss = report.get("peak_rss_kb") if report else None
    return RunResult(
        exit_code=returncode if returncode >= 0 else None,
        signal=-returncode if returncode < 0 else None,
        timed_out=timed_out,
        output_limit_exceeded=output_limit_exceeded,
        time_ms=int((end - start) * 1000),
        peak_rss_kb=peak_rss if isinstance(peak_rss, int) else None,
        report=report,
        stdout=bytes(stdout),
        stderr=bytes(stderr),
    )
