# Code Review Report

## Status
- Target: current worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40` (HEAD confirmed); scoped files listed in implementation evidence.
- Scope: verification of private hint reviewer, model configuration, job deadlines and associated tests; unrelated worktree changes excluded.
- Overall: FINDINGS
- Independent human review: READY with the limitations and follow-up below.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation / type checking | Passed | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync mypy app`, 34 files, exit 0. |
| Tests | Passed | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync pytest -q`, 194 passed in 32.51s, exit 0. In-process, mocked gateway/executor. Coverage gaps below. |
| Smoke/acceptance testing | Blocked | Automated mocked API workflow exercised; live gateway, browser, container and deployed workflow not exercised. Metered live calls require explicit authorization. |
| Static analysis | Passed with limitation | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync ruff format --check .` and `ruff check .`, exit 0. `git diff --check` at root exit 0. Semgrep belongs to security review; no matching completed scan evidence supplied. |
| Packaging/resources | Blocked | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build --offline`, exit 2: required setuptools unavailable in cache. No dependency installation attempted. |
| Specification validation | Passed with limitations | Compared task ACs and backend spec to implementation and tests; acceptance classification below. |
| Documentation consistency | Not applicable | Specialist did not review documentation consistency; assigned to contract review. |

## Acceptance evidence
- AC-01: Supported for existing generator guards and loop by existing tests and empty/canary/strip tests; the gateway is mocked.
- AC-02: Supported for default generator and reviewer request IDs and startup without reviewer in mock model list. Custom overrides and other feature selection are supported by source inspection, not independently exercised end to end.
- AC-03: Unsupported in part: benign markers verify reviewer output placement and tool omission, but hostile delimiter/instruction handling and full request/response secrecy matrix are not exercised (VR-private-hint-01).
- AC-04: Supported by strict parsing and four verdict-combination unit tests; negative verdict is also tested through a job.
- AC-05: Supported at unit level for exception, invalid verdict, canary and timeout and at job level for invalid verdict. Actual network/provider failures are mocked; no live behavior claimed.
- AC-06: Unsupported in part: size, insufficient time, cancellation and ordinary job timeout are individually tested, but the reviewer deadline and runner do not have a combined state-transition test (VR-private-hint-02). Live model availability, gateway input limits and latency are blocked/unverified. Reviewer availability does not block mocked startup.
- AC-07: Supported by bounded loop integration test: four generator requests and one reviewer request.

## Next actions
- Implementation follow-up required: YES (verification tests).
- Edit documentation: NO (within this review axis).
- Rerun code-review skill: AFTER FOLLOW-UP WORK.
- Reason: acceptance tests need to exercise security-boundary adversarial data and the composed reviewer/job deadline.

## Agent handoff
- Follow-up required: YES
- Current implementation/review state: backend checks pass with mocked dependencies; offline build blocked; two coverage findings remain.
- Next responsible skill or human: implement-task owner.
- Priority and findings addressed: Medium, VR-private-hint-01 and VR-private-hint-02.
- Exact files and line locations: `backend/tests/test_student.py:742`, `backend/tests/test_hint_reviewer.py:57`, `backend/app/jobs/runner.py:56`, `backend/app/ai/hints.py:137`.
- Required change or investigation: add outcome-focused integration coverage for hostile data and the reviewer deadline inside a real job; verify protected data stays private and job state reflects the specified outcome.
- Constraints and out-of-scope work: preserve approved fail-open behavior and generator/reviewer separation; no live calls without authorization.
- Verification commands: from `backend/`, `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync pytest -q`, plus configured Ruff and mypy checks; retry offline build when build requirements are cached.
- Manual checks: authorized gateway model availability, bounded latency/input behavior, and deployment smoke remain unverified; use disposable data, never real hidden answers.
- Success criteria: added tests demonstrate expected protected boundaries and final persisted job outcomes, suite passes; explicitly record residual live and build limitations.
- Documentation impact: none identified on this axis.
- Required next rerun: verification review after test changes.
- Blocker or decision needed: cached build dependency and explicit authorization for metered live calls.

## Findings
- `VR-private-hint-01` — [Medium] Hostile reviewer input and private-output boundaries lack the approved integration coverage — Status: Open
- Category: acceptance / security-boundary verification.
- Location: `backend/tests/test_student.py:742`.
- Requirement: AC-03 requires hostile delimiter and instruction content with benign control, fresh spotlighting, and marker inspection across requests; DATA-01 requires reviewer text and hidden data excluded from job/error/log outputs.
- Evidence: the integration test uses ordinary marker strings, checks one generator request for hidden output, one reviewer request for hidden input and output, and failed-job error for one marker. It does not exercise hostile delimiters or instructions, freshness, all generator calls, nor secret reviewer response text across job result/error/log.
- Expected / actual: adversarial data remains within its wrapped data boundary and protected values never appear in public or logged output; current tests establish only a benign subset.
- Reproduction or inspection path: inspect `test_hint_private_reviewer_verdict_and_data_boundary` and `test_review_limits_and_failure_do_not_log_content`.
- Impact: regressions in reviewer data isolation or result/log redaction could pass the suite; mocked tests cannot establish semantic model resistance.
- Likely cause / confidence: planned matrix was only partially implemented; high confidence in the coverage gap.
- Fix direction and affected responsibility: backend test owner should exercise hostile candidate, context and tag-like hidden output plus benign control with distinct markers, inspect every generated request and persisted API result/error/log, and assert fresh wrapping/canaries without copying implementation logic.
- Tests to add/update: integration cases for hostile delimiters and private verdict/hidden-output markers; include generator tool rounds.
- Documentation impact: none.
- Verification after fixing: run focused tests and backend suite; live adversarial behavior remains separate evidence.

- `VR-private-hint-02` — [Medium] Reviewer deadline is not verified through the persisted job lifecycle — Status: Open
- Category: timeout / state-transition verification.
- Location: `backend/tests/test_hint_reviewer.py:57`; `backend/app/jobs/runner.py:56`.
- Requirement: AC-06 requires reviewer timeout before the enclosing job timeout, fail-open on insufficient time, and effective overall deadline and cancellation.
- Evidence: reviewer unit tests call `_review_hint` directly with no deadline or an already expired deadline; cancellation is injected directly. Existing job timeout/shutdown tests use independent handlers. No test combines delayed generator/reviewer calls with runner's computed deadline and persisted outcome.
- Expected / actual: a slow reviewer stops before the job deadline and persists the guarded hint; an actual overall timeout or shutdown still fails the job. These composed behaviors are not exercised.
- Reproduction or inspection path: compare reviewer limit tests with `backend/tests/test_jobs.py` timeout/shutdown tests.
- Impact: regressions in deadline propagation or cancellation handling can fail jobs or persist wrong outcomes while current isolated tests pass.
- Likely cause / confidence: unit-level limits and generic job tests do not cover their integration; high confidence in coverage gap.
- Fix direction and affected responsibility: backend test owner should add deterministic controlled-delay job tests using short budgets and assert persisted status/result and content-free logging, plus cancellation or shutdown while reviewer is active.
- Tests to add/update: reviewer-timeout fail-open within overall deadline, exhausted budget skip, and enclosing cancellation or timeout.
- Documentation impact: none.
- Verification after fixing: focused job/reviewer tests and full backend suite.

## Positive observations
- Tests cover all four verdict combinations, duplicate keys and other invalid schemas, stripped candidate, no review after empty/canary generator output, and a bounded tool loop.
- Reviewer unit tests cover oversize, failure logging, timeout and propagation of cancellation; startup mock excludes the reviewer model.

## Gaps and limitations
- No live model availability, classifier recall, production latency, gateway limits, container, browser, or deployed behavior established. The supplied classifier experiment has only 9 bad and 7 good examples and reports two bad misses.
- No applicable matching Semgrep result was supplied; security reviewer owns scan and triage.
- A discovery command using an unmatched `test_llm*` glob exited 1; subsequent targeted inspection used `rg` over the test directory. It was not a test failure.

## Manual checks for user
- When explicitly authorized, use a disposable environment to verify the configured models exist and a real hint/reviewer workflow respects the documented deadline and data boundary. Assess deployment separately; mocked checks do not prove it.

## Conclusion
- Automated backend checks passed, but the two acceptance coverage gaps and offline packaging limitation prevent a verification PASS.
