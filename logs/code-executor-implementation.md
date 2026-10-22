# Code Executor Implementation Log

Service: `code-execution/` (FastAPI). Spec: `specs/code-execution-spec.md`.
Commits: `350d9f3` (spec), `9f8b1ba` (implementation), `2de7531` (docker run tweak).

## Process (spec-driven)

1. Wrote the spec first (`350d9f3`): API, verdict rules, sandbox design, limits, test plan.
2. Implemented against the spec (`9f8b1ba`).
3. Where the code had to deviate, the spec was updated in the same commit so it stays the source of truth:
   - `python -I` → `-P -s -B`: `-I` also ignores `PYTHONHASHSEED`; the child env is already a fresh dict we control.
   - Peak memory from `VmHWM` in `/proc/self/status`, not `ru_maxrss` (on Linux that survives exec and includes the forked server's RSS).
   - Process exit detected via `pidfd`, not `proc.wait()`, which hangs while leftover child processes hold the pipes open.
   - Report pipe passed as an explicit fd argument instead of a fixed fd 3.
4. `2de7531`: dropped the fixed `MAX_CONCURRENT_JOBS=8` sizing from the README; container now runs with `--memory 16g --cpus 8`.

## What was built

| Module | Role |
|---|---|
| `main.py` | `GET /health`, `POST /v1/execute`; 16 MiB body limit; job semaphore with queue timeout → `503 Retry-After` |
| `auth.py` | Bearer token check (`EXECUTOR_TOKEN`) |
| `judge.py` | Per job: temp workdir, runs tests one by one, stops at the first failure, classifies the verdict (AC / WA / TLE / MLE / RE) |
| `runner.py` | Spawns the harness subprocess, feeds stdin, caps stdout/stderr, enforces the wall timeout, kills the process group |
| `harness.py` | Trusted stdlib-only wrapper in the child: sets rlimits, `exec`s the solution, writes a JSON status report to a pipe |
| `compare.py` | Line/whitespace-normalised comparison, optional abs/rel float tolerance |
| `sanitize.py` | Strips harness frames and workdir paths from tracebacks, truncates messages |

## Security measures (all tested)

- Untrusted code runs in a separate process in its own session; the whole process group is killed after every test.
- rlimits: CPU, address space, file size, open files (64), no core dumps.
- Minimal child env, so `EXECUTOR_TOKEN` and other secrets are never inherited.
- Output caps (stdout ≤ 2× expected, at least 64 KiB, at most 4 MiB; stderr 64 KiB) stop output floods.
- Per-job `0700` temp dir, deleted afterwards; tracebacks are sanitised so server paths don't leak.
- Container: non-root user, `--read-only`, tmpfs work dir, `--cap-drop ALL`, `no-new-privileges`, `--pids-limit`; 

## Resource-aware design

- A semaphore caps concurrent jobs (`MAX_CONCURRENT_JOBS`, default 100); excess requests wait up to `QUEUE_TIMEOUT_S`, then get 503.
- Single uvicorn worker per container (the semaphore is per process); scale out by adding containers.
- Stopping at the first failing test avoids wasted runs; client disconnects cancel the job and kill its processes.

## Testing

`uv run pytest`: **57 passed** (~15 s, Linux).
- `test_api.py`: health, auth, validation, CORS
- `test_verdicts.py`: each verdict, limits, float tolerance
- `test_security.py`: output flood, env secrets, child processes, file writes
- `test_concurrency.py`: parallel jobs, queue timeout, cancellation cleanup
