# Code Execution Service

Judges Python submissions against test cases. See `../specs/code-execution-spec.md`.

## Local dev

```
uv sync
EXECUTOR_TOKEN=... WORK_ROOT=/tmp/executor-work uv run uvicorn app.main:app --port 8001 --workers 1
```

## Tests

The tests start the app in-process with their own token and a temporary work directory, so no env
vars or running server are needed. They do run real submissions with `resource.setrlimit`, so run
them on Linux (or inside the Docker image below), not Windows.

```
uv sync                                  # installs pytest + pytest-asyncio from the dev deps
uv run pytest                            # whole suite
uv run pytest tests/test_verdicts.py     # one file
uv run pytest -k memory_limit -v         # tests whose name matches "memory_limit"
```

The suite is split into `test_api.py` (health, auth, request validation, CORS),
`test_verdicts.py` (judging: accepted, wrong answer, time/memory limits, runtime errors, float
tolerance), `test_security.py` (sandboxing: output floods, env secrets, child processes, file
writes) and `test_concurrency.py` (parallel jobs, queue timeout, cancellation cleanup).

## Docker

The hardening flags (spec §6) are runtime options, so they go on `docker run`:

```
docker build -t code-executor .
docker run -d -p 8001:8001 --env-file .env -e WORK_ROOT=/work \
  --read-only --tmpfs /work:size=256m,mode=1777 --tmpfs /tmp:size=16m \
  --cap-drop ALL --security-opt no-new-privileges:true \
  --pids-limit 512 --memory 16g --cpus 8 code-executor
```
