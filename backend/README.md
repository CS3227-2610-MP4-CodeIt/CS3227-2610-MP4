# Backend

Main API server: accounts, classes, questions, assignments, submissions, AI features.
See `../specs/backend-spec.md`.

## Local dev

Copy `.env.example` to `.env` and fill in `SOCLAAS_API_KEY` and `EXECUTOR_TOKEN` (same value as the
executor's). Start the executor first (`../code-execution/README.md`).

```
uv sync
DATABASE_PATH=./dev.db uv run uvicorn app.main:app --port 8000 --workers 1
```

With `APP_ENV=dev` the demo accounts are created on startup (spec §4): `admin`, `teacher1`,
`teacher2`, `student01`–`student20`, password `demo1234`.

Environment variables override `.env`, so an exported `SOCLAAS_BASE_URL` etc. in your shell wins.

## Tests

The tests start the app in-process with a temporary database and mock SoCLaaS and the executor, so
no env vars, network or running services are needed.

```
uv sync
uv run pytest                          # whole suite
uv run pytest tests/test_student.py    # one file
```

## Docker

Build and run from this folder (it is self-contained):

```
docker build -t backend .
docker run -d -p 8000:8000 --env-file .env -v backend-data:/data \
  --restart unless-stopped backend
```

The SQLite database lives in the `backend-data` volume. Dev and prod use separate env files and
separate volumes (e.g. `backend-data-dev` / `backend-data-prod`); prod sets `APP_ENV=prod` and an
`https://` `CODE_EXECUTION_SERVER` (spec §10, §9.2).

If the executor runs on the same machine, `localhost` inside the container is the container itself.
Use `CODE_EXECUTION_SERVER=http://host.docker.internal:8001` and add
`--add-host host.docker.internal:host-gateway` to `docker run`.
