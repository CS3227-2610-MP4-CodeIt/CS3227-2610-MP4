# Student complexity implementation handoff

Status: IMPLEMENTED — scoped implementation and verification record exist. Independent review has not occurred.

Task: [student-code-complexity-analysis](../tasks/student-code-complexity-analysis.md). Contracts: [backend](../../specs/backend-spec.md), [student frontend](../../specs/frontend/frontend-student.md).

Baseline HEAD: `07ba2c4ca8963133d431359cb04f65ab724e840e`. Pre-existing changes: workflow agent-scope files, eval utilities, security matrix, prototype and task brief. These were preserved; AI-04 in the existing matrix was updated with observed evidence. Review target is the current uncommitted scoped diff plus untracked files listed below; no commit made.

Changed paths: `backend/app/ai/complexity.py`, `backend/app/db.py`, `backend/app/routers/jobs.py`, `backend/app/routers/student.py`, `backend/app/schemas.py`, `backend/backend-schema.sql`, `backend/tests/test_student.py`, `backend/tests/test_complexity_migration.py`, `frontend/src/features/student/QuestionPage.tsx`, `frontend/src/jobs/endpoints.ts`, `frontend/src/jobs/endpoints.test.ts`, `frontend/src/jobs/types.ts`, both linked specs and `workflow/security/security-matrix.md`.

Criteria 1–5 and 7: endpoint checks membership, question and ownership, uses stored completed submission code, and rechecks generic job reads; code-only model call uses wrapping, scan, canary, bounds and no tools. Structured result appears within selected submission, with retry via Analyze. Existing database jobs constraint is migrated retaining IDs and indexes. Specs updated. Mocked test demonstrated non-accepted submitted code, hidden-data exclusion, no tools and wrong role/owner denial. Frontend behavior is source/build evidence only; browser interaction is not verified.

Criterion 6: mocked tests cover injection, benign analysis, malformed/oversized/canary output, missing and other-owner submission and wrong role. Existing generic job tests exercise duplicate/concurrent job creation, but no complexity-specific concurrency test was run. Current-membership removal, wrong-question denial, generic job read revocation, and workspace interaction need focused tests. No live SoCLaaS call was made. No manual browser verification was performed.

Test-first evidence: `backend/.venv/bin/pytest tests/test_student.py -q -k complexity` initially failed because the route returned 404; after implementation it passed. Migration test initially failed due to an invalid test username; corrected fixture passed.

Checks:
- `backend`: `.venv/bin/pytest -q` passed 173 tests before the generic job-read adjustment and migration test addition; `.venv/bin/pytest tests/test_student.py tests/test_jobs.py tests/test_complexity_migration.py -q` passed 58 after those changes.
- `backend`: `.venv/bin/ruff format ...`, `.venv/bin/ruff check app tests/test_student.py`, `.venv/bin/mypy app` passed; last lint/type check preceded the final test addition. `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run pytest ...` failed because locked dependency downloads could not resolve network; existing virtualenv used instead.
- `frontend`: `npm run lint` passed with three existing fast-refresh warnings; `npm run build` passed with chunk-size warning. `npm test` passed 49 tests and `npm run format:check` passed after the endpoint test was added. Build/lint preceded only the test file addition.
- Root: `git diff --check` passed. No browser, deployed or live-model verification.

No review corrections assigned. Remaining work: focused workspace state/snapshot tests, explicit complexity concurrency, current membership and generic read denial tests, browser responsive/snapshot check, final full checks and independent review. Inspect database migration under realistic existing data as part of review.


## Follow-up verification

The earlier limitations concerning focused workspace interaction, membership revocation, wrong-question denial and complexity-specific concurrency were addressed. `backend/tests/test_student.py` adds a six-request concurrent test with a gated mocked handler and verifies one job and one invocation; it also removes membership and verifies GET, POST and generic job read denial. The wrong-question route is denied. The full backend suite after these changes passed 176 tests.

`frontend/e2e/complexity.cjs` uses a local Vite server, mocked API responses and headless Chromium to edit the draft, select two submissions, verify bodyless requests target each selected ID, verify result isolation, exercise failure and retry, and check the mobile panel fits a 390 px viewport. The resulting `/tmp/codeit-complexity-mobile.png` was inspected and the panel was readable. This is a mocked browser check, not live backend/model integration; in-progress display was not separately exercised in the browser.

Final checks: from `backend`, `.venv/bin/ruff format --check .`, `.venv/bin/ruff check .`, `.venv/bin/mypy app`, `.venv/bin/pytest -q` passed (176 tests). An initial Ruff check found an import ordering error; `ruff check --fix tests/test_student.py` resolved it before the passing rerun. From `frontend`, `npm run format:check`, `npm run lint`, `npm test`, `npm run build` passed (49 tests; three existing lint warnings and a build chunk-size warning); lint reran successfully after fixing a warning in the new browser script. With `npm run dev -- --host 127.0.0.1 --port 5179` running, `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH="$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell" node e2e/complexity.cjs` passed outside the sandbox. The default browser executable was unavailable and the sandboxed older browser failed due to macOS Mach port permission; the approved unsandboxed run used the installed executable. Initial browser harness attempts failed due to an overly broad route interception and missing mocked session response; the harness was corrected before the passing run.

Additional changed path: `frontend/e2e/complexity.cjs`. The prior stated need for these tests and browser check is superseded by this section. Live SoCLaaS and deployment are not verified.
