# Code Review Report

## Status
- Target: HEAD `07ba2c4ca8963133d431359cb04f65ab724e840e` plus assigned task changes; supplied aggregate SHA-256 `e7de8a56c3322f41a107d266c177252b4318adeb6252d8b2232d52b972d1538e`, not independently recomputed.
- Scope: Student complexity change; four assigned review axes. Each axis has exactly one supplied artifact.
- Overall: FAIL — security scan blocked; backend packaging and applicable acceptance evidence remain incomplete.
- Independent human review: BLOCKED — required scan and backend package build lack evidence.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Passed by verification reviewer | `frontend`: `npm run build`; chunk-size warning. |
| Tests | Passed by verification reviewer | `backend`: `.venv/bin/pytest -q` (176); `frontend`: `npm test` (49); external services mocked. |
| Smoke/acceptance testing | Incomplete | Implementation handoff reports mocked Chromium and mobile screenshot; verification reviewer did not rerun or inspect them. Loading, real backend integration and other paths remain unverified. |
| Static analysis | Blocked in part | Verification reviewer reports backend Ruff and mypy and frontend format/lint passed; security reviewer reports shared Semgrep failed before scanning with `ca-certs: empty trust anchors`. |
| Packaging/resources | Blocked | Verification reviewer: backend `uv build --offline` could not access default cache; `UV_CACHE_DIR=/tmp/codeit-review-uv-cache uv build --offline` lacked cached `setuptools>=84.2.1`. Executor unchanged. |
| Specification validation | Incomplete | Spec reviewer mapped task criteria; stale reference entries and guard evidence gaps remain. |
| Documentation consistency | Incomplete | `SC-complexity-1` remains open. |

## Next actions
- Implementation follow-up required: YES — migration serialization and focused guard tests.
- Edit documentation: YES — reconcile backend reference.
- Rerun code-review skill: AFTER FOLLOW-UP WORK; security scan and packaging evidence also remain blocked.
- Reason: Three open Medium findings and incomplete required checks.

## Agent handoff
- Follow-up required: YES; security scan and backend packaging are BLOCKED by environment.
- Current implementation/review state: Three open Medium findings; security source review completed without a confirmed finding, but the required scan did not start.
- Next responsible skill or human: implement-task for code and tests; documentation implementer; security and verification reviewers after follow-up.
- Priority and finding addressed: Medium `CQ-complexity-1`, `SC-complexity-1`, `VR-student-complexity-1`; resolve scan and packaging evidence gaps.
- Exact files and line locations: `backend/app/db.py:70`, `backend/tests/test_complexity_migration.py`, `specs/backend-spec.md:225`, `:245`, `:269`, `:816`, `backend/tests/test_student.py:524`, `:554`; scan script `workflow/security/semgrep.sh`.
- Required change or investigation: Recheck migration under the write lock; reconcile backend reference; isolate output guard tests; run and triage the unchanged security scan and retry packaging in a suitable environment.
- Constraints and out-of-scope work: Preserve job records, indexes and contracts; avoid live metered calls, installations, TLS weakening, rule changes and uploads during review.
- Verification commands: From `backend`, `.venv/bin/pytest tests/test_complexity_migration.py -q`, `.venv/bin/pytest tests/test_student.py -q -k complexity`, applicable full checks and `uv build --offline` when cached requirements are available; `git diff --check`; `sh workflow/security/semgrep.sh /tmp/codeit-review-semgrep.json` from repository root. Record scanner version, rules, coverage, exit status and relevant results.
- Manual checks: Exercise loading, submission switching, retry, existing workspace actions, responsive and keyboard presentation with a local backend; live model and deployed behavior when release assurance requires them.
- Success criteria: Concurrent initialization preserves jobs and indexes; references agree with the contract; guard tests detect removal of their controls; packaging and scan have recorded successful evidence and triage.
- Documentation impact: Backend specification requires correction.
- Required next rerun: Code review after follow-up, including security and verification evidence.
- Blocker or decision needed: Semgrep certificate store initialization and missing offline build dependency.

## Findings and axis evidence

### Code quality

Source artifact: `workflow/reviews/student-complexity-run-1/quality.md`.

#### Findings

- `CQ-complexity-1` — Medium: Schema upgrade checks its precondition outside the write lock — Status: Open
- Category: Persistence / concurrency.
- Location: `backend/app/db.py:70`–`80`.
- Requirement: Project standards require explicit transaction boundaries and preservation of asynchronous job state; the task requires the new job kind to remain available.
- Evidence: Each initializer reads the old table SQL and constructs `create` before `BEGIN IMMEDIATE`. Two workers can both read the old schema; after the first commits the upgrade, the second obtains the lock and rebuilds from its stale old SQL. Its replacement adds complexity to that stale SQL, so the rebuilt schema still accepts complexity; however, if the first worker has already inserted a complexity job before the second copies rows, the stale create also includes complexity and preserves the row. The race therefore causes a redundant rebuild rather than a demonstrated failure under the current schema.
- Expected / actual: The schema decision should be made under the same lock as the migration; currently a second migration can run unnecessarily after the upgrade.
- Reproduction or inspection path: Inspect the SELECT, conditional and `BEGIN IMMEDIATE` ordering; concurrent initialization is not exercised by the migration test.
- Impact: Redundant table rebuilds increase startup contention and make the migration dependent on stale schema definitions if additional schema changes are introduced concurrently.
- Likely cause / confidence: Check-before-lock; high confidence in the redundant rebuild, lower confidence in practical impact under current deployment.
- Fix direction and affected responsibility: Recheck the table SQL after acquiring the write lock and skip if already upgraded.
- Tests to add/update: Concurrent old-database initialization test, asserting both initializers complete and jobs and indexes survive.
- Documentation impact: None.
- Verification after fixing: Run the migration test and backend checks.

#### Positive observations

- The frontend panel is scoped by submission key, and the AI result validation is isolated in a dedicated model.
- The migration uses a transaction and explicitly preserves known job indexes.

#### Gaps and limitations

- This was a source review; checks reported by the implementation handoff were not independently rerun. Live model and deployment are unverified.

#### Manual checks for user

- Follow the implementation handoff for live service and deployed behavior; no additional manual check is identified for the code-quality finding.


### Specification and contracts

Source artifact: `workflow/reviews/student-complexity-run-1/spec.md`.

#### Findings

- `SC-complexity-1` — [Medium] Backend reference tables and migration claim are stale — Status: Open
- Category: Documentation / API contract.
- Location: `specs/backend-spec.md:225`, `:245`, `:269`, `:816`.
- Requirement: Acceptance criterion 7 requires the backend specification to document the route and job kind; affected contracts must remain consistent with implementation.
- Evidence: The student endpoint table and job-kind table omit complexity; the generic job table claims any caller-owned job is readable, while `backend/app/routers/jobs.py` rechecks complexity admission. The out-of-scope section says there are no DB migrations, whereas `backend/app/db.py` now upgrades the jobs constraint. The appended complexity section documents the new route but does not reconcile these existing statements.
- Expected / actual: Reference sections consistently describe complexity, its additional generic-read checks, and the limited schema upgrade / existing sections omit or contradict them.
- Reproduction or inspection path: Compare the referenced tables and out-of-scope bullet with the appended section and implementation.
- Impact: Developers using the primary API and deployment reference can miss the new endpoint, assume revoked users can read jobs, or unnecessarily recreate an existing database.
- Likely cause / confidence: New contract appended without integrating existing reference sections; high confidence.
- Fix direction and affected responsibility: Update the affected backend spec tables and qualify the narrow migration exception.
- Tests to add/update: None required for documentation-only correction.
- Documentation impact: Backend specification.
- Verification after fixing: Cross-check updated reference with routes and schema initialization; `git diff --check`.

#### Positive observations

- The selected-submission section follows prototype option 3 and keys analysis by submission ID.
- The model prompt requests auxiliary space and uncertainty; the schema bounds each output field and rejects extra fields.

#### Gaps and limitations

- This review did not independently run checks or recompute the supplied aggregate hash. Test results are attributed to the implementation handoff.
- Mocked checks do not establish live SoCLaaS or deployed integration behavior.

#### Manual checks for user

- Exercise the in-progress state in a browser and verify live model/deployment integration when available.


### Security boundaries

Source artifact: `workflow/reviews/student-complexity-run-1/security.md`.

#### Findings

None confirmed.

#### Positive observations

- Student routes admit only current assignment members and matching owned submissions. A submission row represents a completed verdict; generic complexity job reads repeat the membership and ownership checks. SSE notifications contain job identifiers, kind and target only, not results.
- The model request contains wrapped submitted code only, no tools or hidden tests. Input scan, canary, bounded timeout, token limit and strict output fields provide layered controls. These controls do not prove resistance to every injection.
- Supplied evidence describes mocked denial, input/output validation, deduplication and membership revocation tests; no live-model behavior is inferred from them.

#### Gaps and limitations

- Semgrep CLI exists at `/Users/junhaong/.local/bin/semgrep` but both version check and shared script fail with `ca-certs: empty trust anchors`. The script configures OSS `p/python` and `p/typescript` registry packs for the three application roots; no rules were loaded and no paths scanned in this attempt. Historical scan evidence does not match this target and was not reused.
- This review did not independently execute the supplied tests or verify the supplied digest. Live SoCLaaS, deployment and prompt-injection resistance in a real model remain unverified.

#### Manual checks for user

- A live model and deployed integration check remain optional external evidence, not a task acceptance requirement; review the generated analysis and access revocation there if deployment assurance is needed.


### Verification and evidence

Source artifact: `workflow/reviews/student-complexity-run-1/verification.md`.

#### Findings

- `VR-student-complexity-1` — Medium: Guard tests pass for unrelated validation failures — Status: Open
- Category: Test adequacy / security acceptance.
- Location: `backend/tests/test_student.py:524`, `backend/tests/test_student.py:554`.
- Requirement: Criterion 6 explicitly requires focused output-bound and canary-bearing output fail-closed tests.
- Evidence: The oversized JSON contains only `time_complexity` and therefore also fails required-field validation. The canary response is a bare marker, not a valid JSON result, so it fails JSON parsing even without the canary check. Both assertions only check failed status and no result.
- Expected / actual: Each test should identify its intended control; currently removal of the individual guard could leave the corresponding test green.
- Reproduction or inspection path: Inspect the response fixtures and `backend/app/ai/complexity.py` validation order.
- Impact: The claimed tests cannot detect regression of these controls, leaving explicitly required security acceptance unsupported.
- Likely cause / confidence: Fixtures violate multiple independent constraints; high confidence.
- Fix direction and affected responsibility: Construct schema-valid responses with only the targeted violation, including canary embedded within a valid field and boundary-size cases; retain an ordinary valid control.
- Tests to add/update: Focused canary and response-length/field-length rejection tests with otherwise valid payloads.
- Documentation impact: None.
- Verification after fixing: Run targeted and full backend suites; demonstrate guard-removal mutation causes each targeted test to fail.

#### Positive observations

- Concurrent requests test gates the worker and observes six requests sharing one job and one invocation.
- Membership revocation is checked on both dedicated endpoints and the generic job read. Browser evidence exercises separate submission IDs, retry, and a mobile viewport.
- Migration test establishes that an existing job row survives and the new kind can be inserted with foreign keys consistent.

#### Gaps and limitations

- Existing migration test uses one simple job and does not independently assert preservation of populated fields, IDs, indexes, or related references under realistic data.
- Pending-submission denial, model timeout/recovery, and browser in-progress behavior are not directly established for this feature. Mocked responses do not prove actual analysis quality, live model, deployed behavior, or real backend-to-browser integration.
- No matching Semgrep execution/configuration evidence was supplied to this specialist; security reviewer owns scan and triage.
- The supplied mocked browser run and screenshot were not rerun or independently inspected in this review.

#### Manual checks for user

- With a local test account and backend, verify in-progress presentation, switching submissions while an analysis is running, retry, existing workspace actions, and responsive and keyboard presentation. Verify live/deployed behavior separately if release requires it.

## Conclusion

FAIL: the security axis remains blocked and applicable verification is incomplete. The three Medium findings remain open. Child-reported implementation handoff evidence is not an independent reviewer rerun.
