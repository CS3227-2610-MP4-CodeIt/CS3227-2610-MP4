# Code Review Report

## Status
- Target: HEAD `07ba2c4ca8963133d431359cb04f65ab724e840e` plus task changes, supplied fingerprint `7be3df64cfd9bab36470509ba9ecb72e019608104922861d40d94002d3028b6f`. Verification reviewer verified HEAD; no child independently recomputed the fingerprint.
- Scope: Student complexity feature and correction, including quality, contracts, security boundaries, and verification. Unrelated working-tree changes excluded.
- Overall: **FAIL** — verification axis remains blocked; one Medium documentation finding remains open.
- Independent human review: **BLOCKED** pending applicable integrated browser acceptance and independently accessible backend package build.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Passed | Verification reviewer: `frontend`, `npm run build`, exit 0; chunk-size warning. |
| Tests | Passed, mocked services | Verification reviewer: `backend`, `.venv/bin/pytest -q`, 176 passed; `frontend`, `npm test`, 49 passed. Security reviewer: `backend`, `.venv/bin/pytest tests/test_student.py -q -k complexity`, 6 passed, 25 deselected; model and executor mocked. |
| Smoke/acceptance testing | Blocked in part | Implementation correction handoff reports mocked Chromium checks; verification reviewer did not rerun or inspect them. Real-backend browser flow and visual readability unverified. |
| Static analysis | Passed in part | Verification reviewer: `backend`, `.venv/bin/ruff format --check .`, `.venv/bin/ruff check .`, `.venv/bin/mypy app`; `frontend`, `npm run format:check`, `npm run lint` passed, with three fast-refresh warnings. Security reviewer inspected implementation-agent Semgrep JSON from `sh workflow/security/semgrep.sh /tmp/codeit-correction-semgrep.json`, exit 0 outside sandbox; partial parsing and exclusions limit coverage. |
| Packaging/resources | Blocked in part | Verification reviewer: `backend`, `uv build --offline`, exit 2 due to sandbox cache denial. Correction handoff reports same command passed outside sandbox with existing cache; not independently reproduced. Frontend build passed. Linux executor checks not applicable to unchanged executor. |
| Specification validation | Incomplete | Spec reviewer mapped requirements; contract placement remains contradictory, `SC-complexity-1`. Live model quality and pending state not directly proven. |
| Documentation consistency | Incomplete | `SC-complexity-1`; verification reviewer reports root `git diff --check` passed. |

## Next actions
- Implementation follow-up required: NO.
- Edit documentation: YES.
- Rerun code-review skill: AFTER FOLLOW-UP WORK.
- Reason: Correct the backend specification placement and cross-reference; obtain the blocked acceptance and packaging evidence.

## Agent handoff
- Follow-up required: YES; acceptance and independent packaging evidence BLOCKED pending suitable environments.
- Current implementation/review state: No open code-quality or security finding; prior quality and verification findings fixed. One Medium contract finding open; integrated acceptance and independent packaging remain unverified.
- Next responsible skill or human: Documentation implementer; human with local services and accessible build cache; review aggregator after follow-up.
- Priority and finding addressed: Medium `SC-complexity-1`; blocked verification evidence.
- Exact files and line locations: `specs/backend-spec.md:235`, `specs/backend-spec.md:812`, `specs/backend-spec.md:821`; `frontend/e2e/complexity.cjs`, `backend/tests/test_student.py:505`, `backend/tests/test_complexity_migration.py` for acceptance evidence.
- Required change or investigation: Move the complexity contract to an in-scope section and update its cross-reference; exercise actual local backend/browser and repeat offline packaging with accessible cached dependencies.
- Constraints and out-of-scope work: Preserve the implementation contract; no behavior change needed for documentation. Use disposable data; no metered live model call without authorization and no production changes.
- Verification commands: Inspect heading hierarchy and cross-reference; root `git diff --check`; from `backend`, `uv build --offline`; exercise browser against local services with disposable data.
- Manual checks: Edit draft, select completed submissions, analyze, switch while loading, retry, inspect existing workspace actions, keyboard flow and responsive readability. Live model and deployed access revocation are separate release checks if needed.
- Success criteria: Contract clearly in scope and endpoint reference accurate; stored submission remains the analysis input, states and existing actions work with actual backend, and package build completes.
- Documentation impact: Backend specification correction.
- Required next rerun: Review corrected documentation and reassess affected evidence after new execution or changes.
- Blocker or decision needed: Integrated local environment and accessible build cache.

## Findings

### Code quality
- `CQ-complexity-1` — [Medium] Schema upgrade checks its precondition outside the write lock — Status: Fixed
- Category: Persistence / concurrency.
- Location: `backend/app/db.py:73`.
- Requirement: Explicit transaction boundaries and preservation of asynchronous job state.
- Evidence: `BEGIN IMMEDIATE` now precedes schema lookup and decision; transaction commits after rebuild or skip. Concurrent migration test uses an old WAL database and checks an existing populated row and both indexes.
- Expected / actual: Decision and migration share the write lock / now do so.
- Reproduction or inspection path: Inspect `Database.init_schema` and `backend/tests/test_complexity_migration.py`.
- Impact: Prior stale precondition could cause redundant rebuilding and contention; revised ordering prevents that race.
- Likely cause / confidence: Prior check-before-lock; high confidence in source correction.
- Fix direction and affected responsibility: Completed in database initialization.
- Tests to add/update: Concurrent migration test added.
- Documentation impact: None.
- Verification after fixing: Source inspected; implementation correction handoff reports focused migration test and full backend checks passed; quality reviewer did not rerun them.

### Specification and contracts
- `SC-complexity-1` — [Medium] Complexity contract is nested under out-of-scope — Status: Open
- Category: Documentation / contract.
- Location: `specs/backend-spec.md:235`, `specs/backend-spec.md:812`, `specs/backend-spec.md:821`.
- Requirement: Acceptance criterion 7 requires an accurate backend specification of the new feature and its contract.
- Evidence: New student endpoint table directs readers to §13, headed “Out of scope”; complexity contract is a level-three subsection of that heading. Approved task and implementation establish complexity as in scope.
- Expected / actual: Contract should be in an in-scope section with matching reference; currently under out-of-scope.
- Reproduction or inspection path: Compare endpoint row, heading hierarchy and task acceptance criteria.
- Impact: Developers can interpret the implemented feature as excluded or misunderstand its release status.
- Likely cause / confidence: Appended section after existing final heading; high confidence.
- Fix direction and affected responsibility: Move section into job features area and update cross-reference.
- Tests to add/update: None for documentation correction.
- Documentation impact: Backend specification.
- Verification after fixing: Inspect heading hierarchy and endpoint link, then `git diff --check`.

### Security boundaries
No findings. Existing wildcard CORS scan results at `backend/app/main.py:66` and `code-execution/app/main.py:62` are separately tracked as WEB-01 and EXEC-01; the security reviewer did not report them as new findings for this target.

### Verification and evidence
- `VR-student-complexity-1` — [Medium] Guard tests pass for unrelated validation failures — Status: Fixed
- Category: Test adequacy / security acceptance.
- Location: `backend/tests/test_student.py:505`, `backend/tests/test_student.py:550`.
- Requirement: Criterion 6 requires focused output-bound and canary-bearing output rejection tests.
- Evidence: Field-length payload supplies all required fields; total-size payload decodes to a valid result but escaped JSON exceeds the bound; canary is embedded in an otherwise valid field. Valid response control exists. Correction handoff reports each individual guard-removal mutation made its focused test fail; full suite independently passed.
- Expected / actual: Targeted guards reject otherwise valid responses; corrected fixtures isolate intended conditions.
- Reproduction or inspection path: From `backend`, inspect fixtures and run `.venv/bin/pytest tests/test_student.py -q -k 'complexity_invalid_model_outputs_fail or complexity_canary_leak_fails'`.
- Impact: Original false-positive regression risk addressed.
- Likely cause / confidence: Former fixtures violated multiple constraints; high confidence in correction based on source and reported mutation checks.
- Fix direction and affected responsibility: Completed by implementation agent.
- Tests to add/update: None identified.
- Documentation impact: None.
- Verification after fixing: Full backend suite passed independently; mutation evidence attributed to correction handoff.

## Positive observations
- Model response validation is isolated from routing; frontend panel and job are keyed by selected submission.
- Dedicated endpoints and generic job reads enforce applicable student admission and ownership; model boundaries include validation and resource controls.
- Concurrent analysis test asserts six requests share one invocation and job. Migration test checks preservation of populated data and indexes.
- Previous endpoint, job-kind, generic-read and migration reference omissions were corrected.

## Gaps and limitations
- Four required axis artifacts were supplied; verification remains blocked in part. Aggregator performed no source review or checks.
- Browser evidence uses mocked API responses and was not independently inspected or rerun by verification reviewer; real integration, responsive readability, live model and deployment remain unverified.
- Fresh non-WAL concurrent startup, related-submission foreign-key migration fixture, timeout/recovery, pending submission row and in-flight membership revocation remain unverified. Current migration fixture uses an existing WAL database.
- Security reviewer inspected retained implementation-agent scan JSON, not a reviewer rerun: Semgrep 1.170.0 OSS, `p/python` and `p/typescript`, 225 rules, 111 files, approximately 99.9% parsed; partial parsing at `backend/app/clients/llm.py:122`; Python tests, specs and configuration excluded. Registry rules are mutable and scanning does not prove authorization or injection resistance.
- Mutation checks, external-sandbox package success and mocked browser results are implementation-agent handoff evidence, not independent reviewer reruns. External services were mocked in tests. No live model call was made.

## Manual checks for user
- With disposable local data and a running backend, confirm draft isolation, completed submission analysis, switching during work, failure/retry, existing tabs and actions, keyboard flow and responsive readability.
- Check live model and deployed access revocation separately if release assurance requires them.

## Conclusion
- One open Medium documentation finding and blocked verification evidence prevent a passing review. Two earlier Medium findings are fixed, subject to the evidence limits above.
