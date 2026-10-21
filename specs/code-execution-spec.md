# Code Execution Service — Specification

A standalone microservice that judges Python submissions against test cases, LeetCode-style.
The main backend sends it code + test cases; it runs the code and returns a verdict.

- **Language/runtime:** Python **3.14.4** (pinned; Docker base image `python:3.14.4-slim`), FastAPI, Uvicorn
- **Judged language:** Python 3.14.4 only (the same interpreter as the service, `sys.executable`)
- **Callers:** the main backend only, never browsers. Deployed as its own service, possibly on a
  different host from the backend

---

## 1. Execution model

User code always runs in a **separate child process**, never inside the server's own interpreter
(no in-process `exec`). For each submission:

1. Write the submitted code to `solution.py` in a fresh temporary working directory.
2. For each test case, in order:
   1. Start a new child process with `asyncio.create_subprocess_exec`, running the trusted
      harness (§5.3). The harness applies this test's time and memory limits, then runs `solution.py`.
   2. Write the test's `stdin` contents to the child's stdin pipe and read its stdout and stderr
      through pipes.
   3. Wait for the child to exit, or kill its whole process group with `SIGKILL` when the wall
      timeout fires.
   4. Classify the result (§4.1) and compare stdout against `expected_stdout` (§4.2).
   5. If the test is not `ACCEPTED`, stop and don't run the remaining tests.
3. Delete the working directory and return the verdict.

Starting and waiting on child processes through asyncio doesn't block, so the FastAPI event loop
keeps serving other requests while submissions run. The OS keeps each child's memory separate from
the server, which is what makes it possible to set resource limits, measure time and memory per
test, and kill runaway code without affecting the server.

---

## 2. Architecture

```
backend ──HTTP POST /v1/execute──▶ FastAPI handler (async)
                                        │ validate request
                                        │ async with job_semaphore (100)
                                        ▼
                                   Judge.run(job)
                                        │ for each test case, sequentially:
                                        ▼
                         asyncio.create_subprocess_exec(
                             sys.executable, -I, harness.py, solution.py, limits…)
                                        │ stdin  ← test.stdin
                                        │ stdout → captured (capped)
                                        │ stderr → captured (capped)
                                        │ fd 3   → harness report (JSON)
                                        ▼
                         classify → compare output → stop on first failure
```

### 2.1 Components

| Module | Responsibility |
|---|---|
| `app/main.py` | FastAPI app, routes, startup (creates semaphore, temp root) |
| `app/schemas.py` | Pydantic request/response models and validation bounds |
| `app/config.py` | Settings from env vars (`pydantic-settings`) |
| `app/auth.py` | Internal token dependency |
| `app/judge.py` | Runs a job: creates workdir, loops over tests, aggregates verdict |
| `app/runner.py` | Runs **one** test in a child process; enforces wall timeout; caps output; returns a `RunResult` |
| `app/compare.py` | Output normalisation and comparison |
| `app/sanitize.py` | Rewrites/truncates tracebacks for the error message |
| `app/harness.py` | **Trusted** script executed in the child: applies rlimits, then runs the user's code |

### 2.2 Concurrency model

- All request handlers are `async def`. No blocking calls in the event loop (file writes of the
  small solution file are acceptable; use `asyncio.to_thread` if it ever becomes large).
- A single module-level `asyncio.Semaphore(MAX_CONCURRENT_JOBS)` (default **100**) is created at
  startup. A *job* = one `/v1/execute` request. The handler acquires the semaphore for the whole job
  (all its test cases), so at most 100 user processes exist at any time (tests within a job run
  sequentially, one child at a time).
- Requests beyond 100 wait on the semaphore. If a slot is not obtained within
  `QUEUE_TIMEOUT_S` (default 30 s), return `503 Service Unavailable` with `Retry-After`.
- The semaphore is **per process**. Run Uvicorn with **one worker** (`--workers 1`); otherwise the
  real bound becomes `100 × workers`. Scale horizontally with more containers instead.
- If the client disconnects, the handler's task is cancelled; the runner must catch
  `asyncio.CancelledError`, kill the child's process group, clean up, and re-raise.

---

## 3. API

All endpoints except `/health` require header `X-Internal-Token: <EXECUTOR_TOKEN>`
(compared with `hmac.compare_digest`). Missing/invalid → `401`.

**CORS:** wide open (`CORSMiddleware(allow_origins=["*"], allow_methods=["*"],
allow_headers=["*"])`), so calling it from a browser during dev never hits CORS errors. The
token check above is still what protects it.

### 3.1 `POST /v1/execute`

#### Request (`application/json`)

The backend reads the stored stdin / expected-stdout files and sends their **contents**.

```json
{
  "code": "n = int(input())\nprint(n * 2)\n",
  "time_limit_ms": 2000,
  "memory_limit_mb": 256,
  "float_tolerance": { "abs": 1e-6, "rel": 1e-6 },
  "test_cases": [
    { "stdin": "3\n",  "expected_stdout": "6\n" },
    { "stdin": "10\n", "expected_stdout": "20\n" }
  ]
}
```

| Field | Type | Constraints |
|---|---|---|
| `code` | string | 1 – 64 KiB (UTF-8 bytes), no NUL bytes |
| `time_limit_ms` | int | 100 – 10 000; applies **per test case** |
| `memory_limit_mb` | int | 16 – 1024; applies **per test case** |
| `test_cases` | array | 1 – 100 items |
| `test_cases[].stdin` | string | ≤ 1 MiB; may be empty |
| `test_cases[].expected_stdout` | string | ≤ 1 MiB |
| `float_tolerance` | object \| null | Optional, default `null` (exact comparison). See §4.2.2 |
| `float_tolerance.abs` | float | 0 ≤ abs ≤ 1, default `0` |
| `float_tolerance.rel` | float | 0 ≤ rel ≤ 1, default `0`; at least one of `abs` / `rel` must be > 0 |

`float_tolerance` is a property of the problem: the backend stores it with the problem and sends it
on every request for that problem. The service never guesses whether a problem has float answers.

Total request body ≤ 16 MiB (reject larger with `413` before parsing). Validation failure → `422`.

**Limits are per test case, not per submission.** Every test case runs in its own fresh child
process, and that process gets the full `time_limit_ms` and `memory_limit_mb`. Time and memory
are never added up across tests. For example, with `time_limit_ms = 2000` and 10 tests, each test
may take up to 2 s, so the whole request may legitimately take about 20 s. There is no limit on the
whole run beyond what the backend's HTTP timeout imposes (see §10).

#### Response `200 OK`

A judged submission always returns `200`, whatever the verdict.

```json
{
  "verdict": "RUNTIME_ERROR",
  "passed": 1,
  "total": 2,
  "failed_test_index": 1,
  "error_message": "Traceback (most recent call last):\n  File \"solution.py\", line 1, in <module>\n    n = int(input())\nValueError: invalid literal for int() with base 10: 'abc'",
  "max_time_ms": 41,
  "max_memory_kb": 10240,
  "results": [
    { "index": 0, "status": "ACCEPTED",      "time_ms": 38, "memory_kb": 9980 },
    { "index": 1, "status": "RUNTIME_ERROR", "time_ms": 41, "memory_kb": 10240,
      "stdout_preview": "", "stderr_preview": "Traceback ..." }
  ]
}
```

| Field | Meaning |
|---|---|
| `verdict` | Overall verdict (see §4) |
| `passed` | Number of tests passed before stopping |
| `total` | Number of tests in the request |
| `failed_test_index` | 0-based index of the first failing test; `null` if `ACCEPTED` |
| `error_message` | Sanitised traceback for `RUNTIME_ERROR`; short reason for other failures; `null` if accepted |
| `max_time_ms` / `max_memory_kb` | Largest per-test value over the executed tests (a max, not a sum) |
| `results` | One entry per **executed** test (stops at the first failure; later tests are not run) |
| `results[].stdout_preview` / `stderr_preview` | Only on the failed test, each truncated to 1 KiB. The backend decides whether to show them (e.g. hide for hidden tests). |

#### Other responses

| Code | When |
|---|---|
| `401` | Bad/missing token |
| `413` | Body too large |
| `422` | Validation error |
| `503` | Could not get a semaphore slot within `QUEUE_TIMEOUT_S` |
| `500` | Internal failure of the judge itself (never for user-code failures) |

### 3.2 `GET /health`

No auth. Returns `{"status": "ok", "available_slots": 87, "max_slots": 100}`
(`available_slots` from `semaphore._value` or a counter we maintain).

---

## 4. Verdicts

| Verdict | Condition |
|---|---|
| `ACCEPTED` | Every test exits normally and its output matches |
| `WRONG_ANSWER` | Process exits normally but output does not match `expected_stdout` |
| `TIME_LIMIT_EXCEEDED` | That test's wall time > `time_limit_ms`, or the CPU rlimit killed it (`SIGXCPU`/`SIGKILL` from CPU limit) |
| `MEMORY_LIMIT_EXCEEDED` | Harness reported `MemoryError`, or that test's peak RSS > `memory_limit_mb` |
| `RUNTIME_ERROR` | Uncaught exception (including `SyntaxError`), non-zero `sys.exit`, killed by another signal (e.g. `SIGSEGV`), or output limit exceeded |

`WRONG_ANSWER` is not in the original list but is unavoidable once we compare against expected
stdout, so it is included.

Judging stops at the **first** non-accepted test; that test's status is the overall verdict.

### 4.1 Classification order for one test

Evaluate in this order; the first match wins:

1. Wall timeout fired (we killed it) → `TIME_LIMIT_EXCEEDED`
2. Killed by `SIGXCPU` or harness report says CPU limit → `TIME_LIMIT_EXCEEDED`
3. Harness report says `memory` (caught `MemoryError`) or `peak_rss_kb > memory_limit` → `MEMORY_LIMIT_EXCEEDED`
4. Output cap exceeded → `RUNTIME_ERROR` (`"Output limit exceeded"`)
5. Exit code ≠ 0 or killed by any other signal → `RUNTIME_ERROR` (message = sanitised stderr traceback, or `"Killed by signal SIGSEGV"`)
6. Wall time > `time_limit_ms` (finished but too slow) → `TIME_LIMIT_EXCEEDED`
7. Output mismatch → `WRONG_ANSWER`
8. Otherwise → `ACCEPTED`

### 4.2 Output comparison (`compare.py`)

Comparison is **line by line** in both modes.

#### 4.2.1 Normalisation (always applied to actual and expected)

1. Decode stdout as UTF-8 with `errors="replace"`.
2. Convert `\r\n` → `\n`.
3. Strip trailing whitespace from every line.
4. Strip trailing empty lines.

If the two outputs have a different number of lines → `WRONG_ANSWER`.

#### 4.2.2 Comparing lines

- **`float_tolerance` is `null` (default):** each actual line must equal the expected line exactly.
- **`float_tolerance` is set:** split each pair of lines into tokens on whitespace (`str.split()`).
  The token counts must match. Then, for each pair of tokens (actual `a`, expected `e`):
  - If **both** tokens match the number pattern
    `^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$`, parse them with `float()` and accept if
    `|a − e| ≤ abs` **or** `|a − e| ≤ rel × |e|`. Tolerance is measured against the expected value.
  - Otherwise compare them as exact strings (e.g. `YES`, `nan`, `inf`).

Notes:
- The strict pattern is used instead of trying `float()` because `float()` also accepts
  `inf`, `nan`, `1_000` and padded strings, which would make NaN/inf comparisons unpredictable.
- With a tolerance set, integers count as numbers too, so `3` matches `3.0`. A problem that
  requires exact integer formatting should leave `float_tolerance` unset.
- `float()` overflowing to `inf` for a huge literal (e.g. `1e999`) makes the token fail unless the
  two strings are identical; compare `a == e` as strings first, then numerically.

#### 4.2.3 Wrong-answer message

`error_message` names the first mismatch:
- `"Line count differs: expected 3, got 2"`
- `"Line 3 differs"` (exact mode)
- `"Line 3: expected 4 tokens, got 3"`
- `"Line 3, token 2: expected 0.333333, got 0.334 (|diff| 6.7e-04 exceeds tolerance)"`

Line and token numbers are 1-based. Because messages can reveal expected output, the backend
decides whether to show them (e.g. hide for hidden tests), as with `stdout_preview`.

---

## 5. Running one test (`runner.py` + `harness.py`)

### 5.1 Per-job working directory

- `tempfile.mkdtemp(dir=WORK_ROOT)` with mode `0o700`; write the code to `solution.py`.
- Run every test of the job with `cwd` = this directory.
- `shutil.rmtree` it in a `finally` block (run via `asyncio.to_thread`).

### 5.2 Spawning the child

One child process is spawned **per test case**. The rlimits, wall timeout, timer and peak-RSS
measurement below all apply to that single process, so each test starts with a fresh time and
memory budget.

```python
proc = await asyncio.create_subprocess_exec(
    sys.executable, "-I", "-X", "utf8", HARNESS_PATH,
    "solution.py", str(time_limit_ms), str(memory_limit_mb),
    stdin=PIPE, stdout=PIPE, stderr=PIPE,
    pass_fds=(report_w,),          # harness writes its JSON report here
    cwd=workdir,
    env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"},
    start_new_session=True,        # own process group → we can kill descendants too
)
```

- `-I` (isolated mode): ignore `PYTHON*` env vars and user site-packages, and don't put the
  script's directory on `sys.path` (so a user can't shadow modules).
- `env` is a fresh minimal dict — **never** inherit the server's env (it holds `EXECUTOR_TOKEN`
  and any other secrets).
- `start_new_session=True` so `os.killpg(proc.pid, SIGKILL)` kills any processes the user spawned.
- `preexec_fn` is **not** used (unsafe with threads); limits are applied by the harness instead.

### 5.3 Harness (runs inside the child, trusted code)

```
1. Parse argv: solution path, time_limit_ms, memory_limit_mb, report fd.
2. setrlimit:
     RLIMIT_CPU    = ceil(time_limit_ms / 1000) + 1          (soft), +2 (hard)
     RLIMIT_AS     = (memory_limit_mb + AS_OVERHEAD_MB) MiB   (interpreter baseline ≈ 21 MB VmPeak)
     RLIMIT_FSIZE  = FSIZE_LIMIT (default 1 MiB)              — limits files written to disk
     RLIMIT_NOFILE = 64
     RLIMIT_CORE   = 0
3. Read the source, compile(src, "solution.py", "exec"); run it with
   exec(code_obj, {"__name__": "__main__", "__builtins__": __builtins__}).
4. Catch:
     MemoryError              → report {"status": "memory"}, exit 1
     SystemExit(0 or None)    → treat as normal exit
     SystemExit(other)        → print message to stderr, report {"status": "exit", "code": n}, exit 1
     BaseException            → traceback.print_exc() to stderr, report {"status": "exception"}, exit 1
5. Flush stdout (a failure to flush, e.g. BrokenPipe, → exception).
6. Report {"status": "ok", "peak_rss_kb": getrusage(RUSAGE_SELF).ru_maxrss}; exit 0.
   Every report path includes peak_rss_kb.
```

Running user code via `exec` *inside the child* is fine — the isolation boundary is the process,
not the interpreter.

**Trust note:** user code can write to the report fd or call `os._exit`. This can only *downgrade*
its own verdict (e.g. RE → MLE); it can never produce `ACCEPTED`, because the server measures time
itself and always compares the real stdout. Treat a missing/unparseable report as "no info" and
fall back to exit code/signal.

### 5.4 Parent side

- Feed stdin, read stdout/stderr and the report pipe **concurrently** with bounded readers
  (don't use `communicate()`; it buffers unbounded output):
  - stdout cap = `max(len(expected_stdout) * 2, 64 KiB)`, hard max 4 MiB
  - stderr cap = 64 KiB
  - On exceeding a cap: kill the process group, mark `output_limit_exceeded`.
  - Writing stdin: ignore `BrokenPipeError`/`ConnectionResetError` (program may not read all input).
- Wall timeout: `asyncio.timeout(time_limit_ms / 1000 + WALL_GRACE_S)` (default grace 0.5 s,
  absorbs interpreter start-up ≈ 20–40 ms). On timeout → `os.killpg(pgid, SIGKILL)`, `await proc.wait()`.
- `time_ms` = `time.monotonic()` from this test's spawn to its exit (includes interpreter start-up; documented).
- After exit, always `killpg(SIGKILL)` (ignore `ProcessLookupError`) to reap stragglers that
  daemonised within the group.
- Return:

```python
@dataclass
class RunResult:
    exit_code: int | None        # None if killed by signal
    signal: int | None
    timed_out: bool
    output_limit_exceeded: bool
    time_ms: int
    peak_rss_kb: int | None
    report: dict | None
    stdout: bytes
    stderr: bytes
```

### 5.5 Error message sanitisation (`sanitize.py`)

- Remove traceback frames belonging to `harness.py`.
- Replace the absolute workdir path with nothing so the file shows as `solution.py`.
- Truncate to 4 KiB (keep the **last** 4 KiB — the exception line is at the end).
- Never include server paths, env vars, or other internals.

---

## 6. Security

Running arbitrary code is the main risk. Resource limits stop the code from hurting the *judge*;
they do **not** stop it reading files or using the network, which is why the container itself is
locked down (read-only filesystem, no internet).

| Threat | Mitigation |
|---|---|
| Infinite loop / `sleep` | Wall timeout + `RLIMIT_CPU`; kill whole process group |
| Memory bomb | `RLIMIT_AS`; MemoryError → MLE |
| Fork bomb / spawning children | `start_new_session` + `killpg`; container `pids` limit (`--pids-limit` / `pids.max`, e.g. 512) |
| Huge stdout/stderr | Bounded readers + kill |
| Filling the disk | `RLIMIT_FSIZE`; workdir on a size-limited tmpfs |
| Reading server secrets | Child env is a fresh minimal dict; secrets never written to disk inside the container |
| Shadowing stdlib modules | `python -I`; cwd is the throwaway workdir |
| Unauthorised callers | `X-Internal-Token` on every request; HTTPS in prod so the token and code are not sent in clear text |
| Request flooding | Semaphore + queue timeout → 503; request body size limits |

Container hardening (Dockerfile / compose):
- Run as a non-root user; `read_only: true` root filesystem; `tmpfs: /work:size=256m,mode=1777`.
- `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`.
- Set container-level memory and CPU limits. 100 jobs × 1024 MB worst case won't fit on a small
  host, so choose `MAX_CONCURRENT_JOBS` and the max `memory_limit_mb` together and write down the
  numbers. Then the container limit, not the host, is what absorbs the worst case.
- The executor container must have **no outbound internet** (block egress with the host firewall or
  Docker network rules). It only needs to accept inbound requests from the backend.

---

## 7. Configuration (env vars)

| Variable | Default | Purpose |
|---|---|---|
| `EXECUTOR_TOKEN` | — (required) | Shared secret with the backend |
| `MAX_CONCURRENT_JOBS` | `100` | Semaphore size |
| `QUEUE_TIMEOUT_S` | `30` | Max wait for a slot before 503 |
| `WORK_ROOT` | `/work` | Parent dir for job workdirs |
| `WALL_GRACE_S` | `0.5` | Extra wall time before killing |
| `AS_OVERHEAD_MB` | `32` | Added to `RLIMIT_AS` for interpreter baseline |
| `FSIZE_LIMIT_BYTES` | `1048576` | `RLIMIT_FSIZE` |
| `MAX_STDOUT_BYTES` | `4194304` | Hard stdout cap |

---

## 8. Project layout

```
code-executor/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── schemas.py
│   ├── judge.py
│   ├── runner.py
│   ├── compare.py
│   ├── sanitize.py
│   └── harness.py
├── tests/
│   ├── test_api.py
│   ├── test_verdicts.py
│   ├── test_security.py
│   └── test_concurrency.py
├── Dockerfile
└── pyproject.toml
```

---

## 9. Test plan (pytest + `httpx.AsyncClient`)

### 9.1 Verdicts

| Case | Code | Expected |
|---|---|---|
| Accepted | `print(int(input())*2)` | `ACCEPTED`, all results present |
| Trailing whitespace | prints `"6  \n\n"` vs expected `"6"` | `ACCEPTED` |
| Wrong answer | `print(0)` | `WRONG_ANSWER`, `failed_test_index` correct |
| Stops at first failure | 3 tests, 2nd fails | `results` has 2 entries, 3rd not run |
| Limits are per test | 5 tests, each sleeps 0.8 s, `time_limit_ms=1000` | `ACCEPTED` (≈ 4 s in total, more than the limit, but each test is under it) |
| Memory is per test | 3 tests, each allocates ≈ 40 MB, `memory_limit_mb=64` | `ACCEPTED` |
| Syntax error | `print(` | `RUNTIME_ERROR`, message contains `SyntaxError`, `solution.py` |
| Exception | `1/0` | `RUNTIME_ERROR`, message ends with `ZeroDivisionError`, no harness frames, no workdir path |
| `sys.exit(3)` | | `RUNTIME_ERROR` |
| `sys.exit(0)` mid-way with correct output | | `ACCEPTED` |
| CPU loop | `while True: pass` | `TIME_LIMIT_EXCEEDED` within ~`time_limit + grace` |
| Sleep | `import time; time.sleep(60)` | `TIME_LIMIT_EXCEEDED` |
| Memory | `a = [0] * 10**9` with 64 MB limit | `MEMORY_LIMIT_EXCEEDED` |
| Recursion | deep recursion without limit change | `RUNTIME_ERROR` (`RecursionError`) |
| Doesn't read stdin | `print(6)` with large stdin | `ACCEPTED`, no BrokenPipe crash |

**Float tolerance** (`float_tolerance = {"abs": 1e-6, "rel": 1e-6}` unless stated):

| Case | Actual vs expected | Expected verdict |
|---|---|---|
| Within tolerance | `print(1/3)` vs `0.333333` | `ACCEPTED` |
| Same, no tolerance | `print(1/3)` vs `0.333333`, `float_tolerance` null | `WRONG_ANSWER` |
| Outside tolerance | `0.334` vs `0.333333` | `WRONG_ANSWER`, message names line 1, token 1 |
| Relative tolerance | `1.0000000001e18` vs `1e18` | `ACCEPTED` |
| Absolute only | `1e-9` vs `0`, `{"abs": 1e-6, "rel": 0}` | `ACCEPTED` |
| Integer vs float | `3.0` vs `3` | `ACCEPTED` |
| Mixed tokens | `YES 2.5000001` vs `YES 2.5` | `ACCEPTED` |
| Word mismatch | `NO 2.5` vs `YES 2.5` | `WRONG_ANSWER` |
| NaN as a string | `nan` vs `nan` | `ACCEPTED` |
| NaN vs number | `nan` vs `0.5` | `WRONG_ANSWER` |
| Token count differs | `1 2` vs `1 2 3` | `WRONG_ANSWER` |
| Line count differs | `1\n2` vs `1 2` | `WRONG_ANSWER` |
| Multi-line | 3 lines of floats, each within tolerance | `ACCEPTED` |
| Validation | `{"abs": 0, "rel": 0}`, negative or > 1 values | `422` |

### 9.2 Security

| Case | Expected |
|---|---|
| `while True: print("x"*10**6)` | `RUNTIME_ERROR` "Output limit exceeded", server memory stable |
| `import os; print(os.environ)` | Output contains no `EXECUTOR_TOKEN` |
| Fork bomb (`os.fork()` loop) | Verdict returned; no leftover processes after the job (`ps` check) |
| Spawn a background `sleep 1000` via `subprocess.Popen` | Process is killed after the job |
| Write a 100 MB file | Fails (`RLIMIT_FSIZE`) → `RUNTIME_ERROR` |
| `json.py` in workdir / `sys.path` tricks | Stdlib not shadowed |
| Missing / wrong token | `401` |
| Oversized code / too many tests / bad limits | `413` / `422` |

### 9.3 Concurrency

- Fire 20 concurrent `time.sleep(1)` jobs with `time_limit_ms=2000`: total wall time ≈ 1 s, not
  20 s (proves no blocking).
- While a `while True: pass` job runs, `/health` responds in < 100 ms.
- With `MAX_CONCURRENT_JOBS=2` and `QUEUE_TIMEOUT_S=1`: 3rd concurrent long job gets `503`.
- Cancel a request mid-run: child process is killed and workdir removed.

---

## 10. Out of scope

- Languages other than Python; third-party packages (only the stdlib is available).
- Special/custom checkers, whitespace-insensitive (token stream) comparison, case-insensitive
  comparison, interactive problems.
- Persisting submissions (the backend owns storage).
- Logging, metrics and monitoring.
- Async job queue / polling API (requests are synchronous; max ≈ 100 tests × 10 s, so the backend
  must set its HTTP client timeout to at least
  `len(test_cases) × (time_limit_ms / 1000 + WALL_GRACE_S) + QUEUE_TIMEOUT_S`, plus a margin).
