# Specification and Contract Review

## Status
- Target: scoped current worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`.
- Scope: private hint reviewer implementation, tests, backend specification and Developer Guide; unrelated work excluded.
- Overall: BLOCKED: source-level contracts are mapped, but live classifier and deployment acceptance remain limited.
- Independent human review: BLOCKED pending assessment of live false negative and other review axes.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation, tests, static analysis | Not independently run | Outside this specialist axis; follow-up report records 200 mocked backend tests and static checks. |
| Packaging/resources | Reported passed | Supplied live evidence reports `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build` succeeded; not independently rerun. |
| Smoke/acceptance testing | Partial | Supplied synthetic live probe exercised catalog, generator tools and reviewer; no deployed or persisted production job. |
| Specification validation | Partial | AC-01–07 mapped below; classification reliability and real latency remain unproven. |
| Documentation consistency | Verified by inspection | Changed spec and guide compared with implementation and approved task. |

## Requirement mapping
- AC-01, AC-07 — Verified by source and test inspection: generator guards and three-round limit precede review; empty hints fail; tests distinguish generator and reviewer calls. Execution evidence in the supplied follow-up report is mocked.
- AC-02 — Verified by inspection: separate model settings and generator override; global model retained for other calls; reviewer not checked at startup. Live evidence reports both configured IDs present and generator tool calls functioning for one synthetic case.
- AC-03 — Verified by inspection: reviewer receives question context, guarded candidate and hidden expected outputs, without hidden input fields or tools; fresh nonce/canary and lossless encoded spotlighting are used. Synthetic hostile-tag case was withheld, but one case cannot establish injection resistance.
- AC-04 — Verified by inspection: exactly two actual boolean fields, no duplicates; negative verdict withholds. Live probe observed valid verdicts. A valid verdict is not proof of accurate classification: a complete working-code solution was allowed.
- AC-05 — Verified by inspection: reviewer errors, invalid verdicts, canary leaks and timeout fail open with content-free logs; generator guard remains mandatory. Live failure paths were not exercised by the supplied probe.
- AC-06 — Verified by inspection: 64 KiB payload bound, 20-second reviewer limit, one-second margin, skip on insufficient time, cancellation not caught. Four reviewer samples of 0.12–0.13 seconds do not establish tail latency or gateway size limits.
- Spec §§7.1 and 8 and Developer Guide: verified by inspection against changed configuration, startup, data flow and resource limits. Assignment deployment separation is unaffected; deployed behavior is not established.

## Next actions
- Implementation follow-up required: NO for a confirmed contract defect; human assessment of observed false negative remains necessary.
- Edit documentation: NO for a confirmed inconsistency.
- Rerun code-review skill: AFTER FOLLOW-UP WORK if behavior or documentation changes.
- Reason: Approved contract specifies the reviewer verdict handling and explicitly acknowledges misses; live evidence demonstrates a residual risk, not a violation of a specified accuracy threshold.

## Agent handoff
- Follow-up required: BLOCKED for full acceptance and risk assessment.
- Current implementation/review state: No open contract findings; previous two specification findings remain fixed by inspection.
- Next responsible skill or human: AI owner and independent human reviewer.
- Priority and finding addressed: Assess live false negative and approved fail-open residual disclosure risk.
- Exact files and line locations: `backend/app/ai/hints.py:21`, `backend/app/ai/hints.py:139`, `workflow/live-ai/hint-current-pipeline-2026-11-09.md`.
- Required change or investigation: Decide whether observed solution disclosure is acceptable and whether further representative synthetic evaluation or a revised requirement is needed.
- Constraints and out-of-scope work: Do not treat classifier as an enforcement guarantee or change approved fail-open policy without direction; preserve privacy and unrelated work.
- Verification commands: Supplied probe command is `.venv/bin/python ../workflow/live-ai/hint-current-pipeline-probe.py` from `backend/`; use synthetic data and record limitations.
- Manual checks: Assess deployed workflow, live error paths, reviewer accuracy, provider retention and production latency as applicable.
- Success criteria: Human explicitly assesses residual risk and outstanding evidence; other review axes resolved.
- Documentation impact: Update claims if behavior or acceptance decision changes; do not describe probabilistic classification as guaranteed.
- Required next rerun: After relevant follow-up changes or evidence.
- Blocker or decision needed: Human risk acceptance and representative live/deployment evidence.

## Findings
- `SC-private-hint-1` — [High] Reviewer can receive a different candidate from the hint returned — Status: Fixed
- Category: Acceptance contract / protected answer review.
- Location: `backend/app/ai/hints.py:144`.
- Requirement: Reviewer receives the guarded candidate faithfully.
- Evidence: JSON encoding escapes angle brackets before spotlighting; hostile-content test checks round-trip fidelity.
- Expected / actual: Tag-like candidate content is preserved rather than removed.
- Reproduction or inspection path: Inspect `_review_hint` and hostile-content test.
- Impact: Previously identified content mismatch corrected for the reviewed path.
- Likely cause / confidence: Encoding avoids destructive tag removal; high confidence by inspection.
- Fix direction and affected responsibility: Completed in reviewer payload construction.
- Tests to add/update: Hostile-content round-trip test exists.
- Documentation impact: Spec documents encoding.
- Verification after fixing: Source and test inspected; follow-up report records suite execution.

- `SC-private-hint-2` — [Medium] Developer Guide describes obsolete model configuration and hint data flow — Status: Fixed
- Category: Developer documentation.
- Location: `docs/DeveloperGuide.md:88`.
- Requirement: Developer instructions reflect model configuration and protected data flow.
- Evidence: Guide names generator and reviewer settings, startup checks, fail-open behavior, boundaries and limits.
- Expected / actual: Guide aligns with reviewed source and spec.
- Reproduction or inspection path: Compare guide with configuration, startup and hint implementation.
- Impact: Prior misleading setup and data-flow claims corrected.
- Likely cause / confidence: Documentation updated alongside implementation; high confidence by inspection.
- Fix direction and affected responsibility: Completed in Developer Guide.
- Tests to add/update: None required for documentation correction.
- Documentation impact: Correction complete.
- Verification after fixing: Compared documented claims with source.

## Positive observations
- The spec describes reviewer-only hidden outputs and the approved fail-open exception; the guide qualifies reviewer quality.
- Live evidence establishes model catalog availability and a synthetic tool-call path, superseding the earlier absence of all live evidence.

## Gaps and limitations
- One live full-solution candidate was allowed. Approved requirements contain no accuracy threshold, so this is a significant demonstrated residual risk requiring human assessment, not a newly asserted contractual defect.
- Small samples do not establish recall, injection resistance, provider retention or production tail latency; no deployed service or persisted production job was exercised. This reviewer did not run tests or the probe.

## Manual checks for user
- Review observed false negative and fail-open risk; evaluate representative synthetic cases and deployed behavior, including failure and timeout paths, as needed for release.

## Conclusion
- No open specification findings; full acceptance remains blocked by unresolved evidence and human risk assessment.
