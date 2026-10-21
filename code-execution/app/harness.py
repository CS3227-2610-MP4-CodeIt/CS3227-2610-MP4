"""Trusted wrapper run in the child process: applies rlimits, then runs the user's solution.

argv: solution_path time_limit_ms memory_limit_mb as_overhead_mb fsize_limit_bytes report_fd
Imports only the stdlib; never import from the app package here.
"""

import json
import math
import os
import resource
import sys
import traceback


def set_limit(res: int, soft: int, hard: int) -> None:
    _, current_hard = resource.getrlimit(res)
    if current_hard != resource.RLIM_INFINITY:
        soft, hard = min(soft, current_hard), min(hard, current_hard)
    resource.setrlimit(res, (soft, hard))


def peak_rss_kb() -> int:
    # VmHWM resets on exec; ru_maxrss would include the forked server's RSS.
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1])
    except OSError:
        pass
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def report(fd: int, payload: dict) -> None:
    payload["peak_rss_kb"] = peak_rss_kb()
    try:
        os.write(fd, json.dumps(payload).encode())
        os.close(fd)
    except OSError:
        pass


def main() -> None:
    solution_path = sys.argv[1]
    time_limit_ms, memory_limit_mb, as_overhead_mb, fsize_limit, report_fd = map(int, sys.argv[2:7])

    cpu_s = math.ceil(time_limit_ms / 1000) + 1
    set_limit(resource.RLIMIT_CPU, cpu_s, cpu_s + 1)
    address_space = (memory_limit_mb + as_overhead_mb) * 1024 * 1024
    set_limit(resource.RLIMIT_AS, address_space, address_space)
    set_limit(resource.RLIMIT_FSIZE, fsize_limit, fsize_limit)
    set_limit(resource.RLIMIT_NOFILE, 64, 64)
    set_limit(resource.RLIMIT_CORE, 0, 0)

    sys.argv = [solution_path]
    status: dict = {"status": "ok"}
    exit_code = 0
    try:
        with open(solution_path, encoding="utf-8") as f:
            source = f.read()
        code_obj = compile(source, solution_path, "exec")
        try:
            exec(code_obj, {"__name__": "__main__", "__builtins__": __builtins__})
        except SystemExit as e:
            if e.code not in (0, None):
                raise
        sys.stdout.flush()
    except MemoryError:
        status, exit_code = {"status": "memory"}, 1
    except SystemExit as e:
        if isinstance(e.code, int):
            status = {"status": "exit", "code": e.code}
        else:
            print(e.code, file=sys.stderr)
            status = {"status": "exit", "code": 1}
        exit_code = 1
    except BaseException:
        traceback.print_exc()
        status, exit_code = {"status": "exception"}, 1

    try:
        sys.stdout.flush()
    except BaseException:
        if exit_code == 0:
            traceback.print_exc()
            status, exit_code = {"status": "exception"}, 1
    try:
        sys.stderr.flush()
    except BaseException:
        pass
    report(report_fd, status)
    # os._exit skips user atexit handlers and doesn't wait on user threads.
    os._exit(exit_code)


main()
