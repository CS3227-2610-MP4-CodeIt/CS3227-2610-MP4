# admin-summary-response-reliability — reject unusable Admin summary responses

Status: READY. User reviewed the 18-case baseline (7 passed, 11 assertion failures, no errors) and explicitly approved Task 1 implementation on 2026-11-06. Acceptance remains subject to verification and independent review.
Owner: main for planning/baseline; existing task_implementer after authorization.
Depends on: no other task; Task 2 explicitly deferred.
Sources: user scope approval; backend spec §§7.3, 8, 9.1; frontend Admin spec §2; assignment-brief.md.
Baseline: `818fd61111677f1e8221776226ef09aa54e1b8b4`, branch `feature/admin-ai-reliability`, clean initial worktree.

## Outcome and scope

Current summary handler accepts blank output, ignores completion metadata and silently slices long text through the shared guard. Introduce summary-specific response validation only after approval. Preserve API shape `{stats, summary_md}`, SQL aggregates, database schema, shared jobs, authorization, Teacher/Student behavior, retry policy and 512-token cap.

Spec delta: [proposed contract and traceability](../planning/admin-summary-response-reliability.md). Canonical specs are unchanged pending baseline review.

Decisions: fail safely rather than truncate or repair; use a summary-specific validator; no extra generation call. Completion requires `stop`, no tool calls, nonempty trimmed text, ≤150 whitespace-delimited words and ≤2000 characters. Character boundary fixtures are structural tests, not examples of semantically useful prose. Statistical ranking/zero/tie interpretation is Task 2, excluded.

## Acceptance and planned verification

The linked traceability matrix defines AC-01 through AC-08 and their fixture IDs. Run from backend: `uv run --locked pytest -q -s tests/test_admin_summary_reliability.py`; preserve stdout and JUnit XML, including nonzero exit status. Existing regression command and evidence are in the baseline record.

## Implementer handoff

Implementation authorized: production scope is backend/app/ai/summary.py ONLY. Add a private typed validator: full original text canary check first, require finish_reason == stop, reject tool calls, trim then reject empty, >150 whitespace-delimited words or >2000 Python Unicode characters, preserve accepted trimmed text. New validation failures use exactly "The AI summary response was rejected. Try again." Preserve existing canary and already-safe malformed response errors. No repair/model calls. Original 18 baseline cases must remain unchanged; add supplemental tests separately. Baseline evidence: workflow/planning/admin-summary-fcfbbe564ef745c29e3f3fd5aa7d35c8/. Own summary.py and supplemental tests only; not alone in repository, preserve all other work. No shared client, guard, repository, schema, infrastructure, canonical spec or frontend edits. Stop for separate approval if required. Docker previously unavailable in agent PowerShell; prepare manual commands if still unavailable. Do not modify running containers/volumes or access env files/credentials. No commit/logging closeout approval inferred.

Independent review uses existing code_quality_reviewer, spec_contract_reviewer, security_boundary_reviewer and verification_reviewer profiles on one fixed target, then review_aggregator. Schedule within concurrency limits; freeze writers during review; at most two correction passes. Do not create duplicate agent functionality. No commit, push, merge or branch switch.

## Final acceptance addendum — 7 November 2026 (Asia/Singapore)

The user accepted Task 1 as **PASS WITH LIMITATIONS (WARN)**. This dated addendum supersedes the earlier pending-verification and pending-baseline-review wording above; the original specification, approval and handoff history is preserved. Canonical specifications remain unchanged and require separate approval to edit.

| Recorded experiment/check | Final result |
| --- | --- |
| Original 18-case contract experiment | Before: 7 passed / 11 failed; after: 18/18 passed |
| Supplemental response-validation cases | 16/16 passed |
| Full backend regression on formatted target | 168/168 passed, 90.87 seconds |
| Ruff format/lint, mypy and offline package build | Passed; 47 formatting files, 33 mypy source files; cached setuptools 84.2.1 |
| Current-target Semgrep | Completed with two pre-existing wildcard-CORS findings and one documented partial-parsing limitation; not a clean scan |

The final [security closeout](../reviews/admin-summary-task1-security-closeout.md) records the independent assessments, resolved evidence gates and residual risks. Only `backend/app/ai/summary.py` changed in production; the original test contract was preserved through formatting-only edits. Shared behavior, retries and the 512-token budget remain unchanged, with no repair call added.

Acceptance is limited to the verified mocked backend behavior. The two baseline CORS risks remain open for separate production-origin/private-executor decisions. The unchanged `llm.py` parsing limitation has manual review and executed test compensation, not complete static coverage. No production-security, deployed-isolation, live-provider or factual-prose guarantee is made. Task 2 remains deferred; raw run evidence stays local. See the [runner README](../scripts/README.md) for reproduction instructions and evidence limits.
