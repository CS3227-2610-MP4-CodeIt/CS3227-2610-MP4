# Code Review Report

## Status
- Target: HEAD `07ba2c4ca8963133d431359cb04f65ab724e840e` plus assigned task changes; supplied aggregate SHA-256 `e7de8a56c3322f41a107d266c177252b4318adeb6252d8b2232d52b972d1538e`.
- Scope: Code-quality axis across the changed backend AI, database, job and student routes, schemas, and frontend job and submission panel implementation.
- Overall: FINDINGS
- Independent human review: READY

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Not independently run | Implementation handoff records backend and frontend checks. |
| Tests | Not independently run | Reviewed migration test and implementation handoff; concurrency of schema upgrade is not covered. |
| Smoke/acceptance testing | Not independently run | Handoff records mocked browser verification. |
| Static analysis | Not independently run | Handoff records Ruff, mypy and frontend lint checks. |
| Packaging/resources | Not assessed | Outside this specialist axis. |
| Specification validation | Not assessed | Outside this specialist axis; task brief consulted for context. |
| Documentation consistency | Not assessed | Outside this specialist axis. |

## Next actions
- Implementation follow-up required: YES
- Edit documentation: NO
- Rerun code-review skill: AFTER FOLLOW-UP WORK
- Reason: Concurrent startup can perform a redundant database rebuild using a stale schema definition.

## Agent handoff
- Follow-up required: YES
- Current implementation/review state: One open migration concurrency finding.
- Next responsible skill or human: implement-task.
- Priority and finding addressed: Medium, CQ-complexity-1.
- Exact files and line locations: `backend/app/db.py:70`; `backend/tests/test_complexity_migration.py`.
- Required change or investigation: Acquire the migration write lock before reading and deciding the schema version, then re-read under the lock; make the upgrade idempotent across concurrent initializers.
- Constraints and out-of-scope work: Preserve existing job records and indexes; keep unrelated schema behavior unchanged.
- Verification commands: `cd backend && .venv/bin/pytest tests/test_complexity_migration.py -q`, then relevant backend checks.
- Manual checks: No additional manual check specific to this finding; mocked browser and live service limits remain as recorded in the handoff.
- Success criteria: Concurrent initializers on an old database leave the complexity kind enabled and preserve existing and newly created jobs.
- Documentation impact: None expected.
- Required next rerun: Code review after correction.
- Blocker or decision needed: None.

## Findings
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

## Positive observations
- The frontend panel is scoped by submission key, and the AI result validation is isolated in a dedicated model.
- The migration uses a transaction and explicitly preserves known job indexes.

## Gaps and limitations
- This was a source review; checks reported by the implementation handoff were not independently rerun. Live model and deployment are unverified.

## Manual checks for user
- Follow the implementation handoff for live service and deployed behavior; no additional manual check is identified for the code-quality finding.

## Conclusion
- The upgrade decision should be serialized with the rebuild to avoid redundant work and reliance on a stale schema definition.
