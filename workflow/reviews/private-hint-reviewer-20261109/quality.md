# Code Review Report

## Status
- Target: current worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`.
- Scope: code-quality axis for the assigned backend configuration, LLM client, hint reviewer, job runner, startup and tests; related spec and supplied task/evidence inspected for context.
- Overall: FINDINGS
- Independent human review: READY, subject to the limitations below.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Implementation and async boundaries | Complete | Inspected scoped diff and affected hint, client, startup and runner paths. |
| Static analysis | Complete | `cd backend && UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --no-sync ruff check .` and `uv run --no-sync mypy app` passed; `git diff --check` passed. |
| Compilation | Not independently run | Implementer reports mypy success. |
| Tests | Not independently run | Implementation evidence reports 194 backend tests passed, followed by one focused test after a test-only change. |
| Smoke/acceptance testing | Not independently run | Mocked tests and limitations are described in implementation evidence. |
| Packaging/resources | Unverified | Implementation evidence reports offline build blocked by missing setuptools. |
| Specification validation | Context inspected | Full contract review belongs to the assigned specialist. |
| Documentation consistency | Context inspected | Full documentation review belongs to the assigned specialist. |

## Next actions
- Implementation follow-up required: YES
- Edit documentation: NO
- Rerun code-review skill: AFTER FOLLOW-UP WORK
- Reason: distinguish expected fail-open reviewer failures from unexpected implementation defects while preserving content-free logging.

## Agent handoff
- Follow-up required: YES
- Current implementation/review state: reviewer failure handling masks unexpected defects as normal fail-open outcomes.
- Next responsible skill or human: implement-task.
- Priority and finding addressed: Medium, CQ-private-hint-reviewer-01.
- Exact files and line locations: `backend/app/ai/hints.py:168`–`186`.
- Required change or investigation: narrow expected exceptions or explicitly distinguish unexpected errors with a safe, content-free diagnostic; preserve approved fail-open behavior for reviewer failures.
- Constraints and out-of-scope work: never log protected inputs, provider output or exception text; preserve cancellation and approved reviewer failure behavior.
- Verification commands: `cd backend && UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --no-sync pytest -q tests/test_hint_reviewer.py tests/test_student.py` and relevant Ruff/mypy checks.
- Manual checks: Live gateway availability, real reviewer reliability and production latency remain unverified; mocked checks cannot establish these.
- Success criteria: expected failures and unexpected implementation failures remain content-free and distinguishable; cancellation and fail-open tests pass.
- Documentation impact: none anticipated.
- Required next rerun: code-quality review after follow-up.
- Blocker or decision needed: none.

## Findings
- `CQ-private-hint-reviewer-01` — [Medium] Unexpected reviewer bugs are indistinguishable from expected fail-open failures — Status: Open
- Category: Error handling and operator diagnostics.
- Location: `backend/app/ai/hints.py:168`–`186`.
- Requirement: Project standards call for deliberate failure handling and protected diagnostics; approved task requires call, timeout and invalid-verdict failures to fail open with content-free logging.
- Evidence: One `except Exception` encloses the gateway call, response field access, canary check and JSON/schema parsing and logs the same warning for all exceptions. An `AttributeError` or other programming defect in these operations therefore follows the same path as a gateway failure or malformed verdict.
- Expected / actual: Expected operational failures should remain safely fail-open while unexpected implementation failures are distinguishable without logging sensitive exception content. Currently both silently return the candidate with identical warnings.
- Reproduction or inspection path: Have the reviewer call or returned reply raise an unexpected `AttributeError`; `_review_hint` returns normally and logs the generic reviewer warning, just as for a malformed verdict.
- Impact: A regression can disable the reviewer across requests while appearing to be ordinary transient reviewer failure, delaying diagnosis of an unreviewed-hint path.
- Likely cause / confidence: Broad catch combines the external I/O and internal parsing boundaries; high confidence from inspection.
- Fix direction and affected responsibility: Classify expected gateway, timeout and verdict errors separately from unexpected internal errors; keep all diagnostic messages content-free and preserve approved fail-open behavior and cancellation semantics.
- Tests to add/update: Simulate an unexpected internal error and an expected reviewer error; verify distinct safe diagnostics and unchanged returned-hint behavior, with no protected content in logs.
- Documentation impact: none anticipated.
- Verification after fixing: focused reviewer and student tests, Ruff and mypy; inspect logs for absence of exception text and protected content.

## Positive observations
- Reviewer receives a separate tool-free call with fresh spotlighting and canary; strict verdict parsing rejects duplicate keys and non-boolean fields.
- Job deadlines use the event-loop clock and reviewer cancellation is not swallowed by the `Exception` handler.

## Gaps and limitations
- This specialist reviewed code quality only; security, specification and verification decisions belong to their respective reviewers.
- Live model availability, reviewer quality, gateway limits and latency remain unverified, as recorded in implementation evidence. Package build remains unverified.

## Manual checks for user
- Check configured generator and reviewer availability and representative reviewer behavior against the actual gateway when credentials are available; assess deployment latency separately.

## Conclusion
- One medium code-quality finding requires follow-up; no Blocker or High finding was identified on this axis.
