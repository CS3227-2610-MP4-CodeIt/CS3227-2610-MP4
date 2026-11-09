# Specification and Contract Review

## Status
- Target: scoped current worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`, including the assigned Developer Guide correction.
- Scope: private hint reviewer task, backend contract and affected developer documentation; unrelated work excluded.
- Overall: BLOCKED on live acceptance evidence; no open specification findings identified by inspection.
- Independent human review: BLOCKED pending assessment of the limitations and the other review axes.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation, tests, static analysis, packaging | Not independently rerun | Outside this specialist axis. Prior implementation evidence reports mocked tests and checks, but precedes corrections; offline build was unavailable. |
| Smoke/acceptance testing | Partial | Source and tests inspected; live gateway model availability, tool support, latency and classifier behavior remain unverified. |
| Specification validation | Partial | Mapped AC-01–07 to implementation and test source below; actual model behavior requires live evidence. |
| Documentation consistency | Verified by inspection | Compared changed Developer Guide and backend spec with configuration, startup and hint implementation. |

## Requirement mapping
- AC-01 and AC-07: Generator loop, tools and guards remain in place; empty/rejected candidates precede the reviewer. Tests describe four generator calls and one reviewer call. Verified by source inspection; execution after corrections not independently verified.
- AC-02: Separate configured model overrides, default model for other features and startup checks are present. Reviewer availability is not a startup prerequisite. Verified by source inspection; live model availability not verifiable here.
- AC-03: Reviewer receives question context, hidden expected outputs and the guarded candidate, no hidden input fields or tools; fresh nonce and canary are used. JSON encoding escapes angle brackets before spotlighting, preserving tag-like candidate and output text. Hostile-content test checks round-trip fidelity and privacy. Verified by inspection; model adherence to instruction/data separation is not verifiable from mocks.
- AC-04: Parser requires exactly two boolean fields and rejects duplicate keys; valid negative verdict raises a safe retry error. Verified by inspection and test source.
- AC-05: Reviewer errors, malformed verdict, canary leak and timeout fail open with content-free categories; negative verdict is withheld. Verified by inspection and test source.
- AC-06: Payload is capped at 64 KiB without truncation; reviewer timeout is at most 20 seconds and reserves one second before job deadline. Insufficient budget skips review; cancellation remains outside the caught exceptions. Source and tests inspected; gateway limits and live latency are unverified. The implementation evidence identifies the cap as a conservative local bound and latency data as limited.
- Assignment deployment separation is unaffected by the scoped changes. Developer Guide model defaults, startup requirements, reviewer data flow and limits agree with the implementation. Spec §7.1 and §8 reflect the approved reviewer exception and fail-open policy.

## Next actions
- Implementation follow-up required: NO on this axis.
- Edit documentation: NO on this axis.
- Rerun code-review skill: NO on this axis unless further relevant changes are made.
- Reason: Both prior specification findings are corrected by inspection; live behavior is still an explicit limitation.

## Agent handoff
- Follow-up required: BLOCKED for live acceptance evidence.
- Current implementation/review state: No open specification findings; source-level contract mapping complete, live behavior unverified.
- Next responsible skill or human: AI owner and independent human reviewer.
- Priority and finding addressed: Live acceptance limitation; `SC-private-hint-1` and `SC-private-hint-2` fixed by inspection.
- Exact files and line locations: `backend/app/ai/hints.py` reviewer and generator; `docs/DeveloperGuide.md` setup and AI configuration; `specs/backend-spec.md` §§7.1 and 8.
- Required change or investigation: Verify model availability, generator tool support, reviewer classification and latency with authorized synthetic data; assess residual fail-open risk.
- Constraints and out-of-scope work: Preserve protected content, approved fail-open behavior and unrelated work.
- Verification commands: Relevant focused and full backend checks after corrections are for the verification reviewer; live checks require authorized gateway access.
- Manual checks: Synthetic live gateway and deployed workflow checks remain unverified.
- Success criteria: Acceptance evidence and residual risks reviewed by a human; other review axes resolved.
- Documentation impact: None identified on this axis.
- Required next rerun: After relevant follow-up changes.
- Blocker or decision needed: Live gateway evidence is unavailable in the supplied record.

## Findings
- `SC-private-hint-1` — [High] Reviewer can receive a different candidate from the hint returned — Status: Fixed
- Category: Acceptance contract / protected answer review.
- Location: `backend/app/ai/hints.py`, `_review_hint`.
- Requirement: Reviewer receives the guarded candidate faithfully.
- Evidence: `encode_data` JSON-encodes and escapes angle brackets before `wrap_untrusted`; the hostile-content test decodes and compares the candidate and hidden outputs with originals.
- Expected / actual: Tag-like text is preserved as JSON escapes rather than removed by the spotlighting guard.
- Reproduction or inspection path: Inspect `_review_hint` and `test_hint_reviewer_hostile_content_is_lossless_and_private`.
- Impact: The previously identified omission of tag-like candidate text is corrected for the reviewed path.
- Likely cause / confidence: Prior destructive tag filtering avoided through encoding; high confidence in the source-level correction.
- Fix direction and affected responsibility: Completed in reviewer payload construction.
- Tests to add/update: Hostile-content round-trip test added; execution after corrections not independently verified.
- Documentation impact: Spec documents encoding.
- Verification after fixing: Source and test inspected; independent test execution remains for verification review.

- `SC-private-hint-2` — [Medium] Developer Guide describes obsolete model configuration and hint data flow — Status: Fixed
- Category: Developer documentation.
- Location: `docs/DeveloperGuide.md` setup and AI configuration sections.
- Requirement: Developer instructions reflect actual model configuration and protected data flow.
- Evidence: Guide now names generator and reviewer settings, startup checks, fail-open behavior, data boundaries and resource limits matching source and spec.
- Expected / actual: Correct configuration and reviewer context are documented.
- Reproduction or inspection path: Compare guide with `backend/app/config.py`, `backend/app/main.py` and `backend/app/ai/hints.py`.
- Impact: Prior misleading setup and data-flow claims corrected.
- Likely cause / confidence: Guide updated alongside implementation; high confidence by inspection.
- Fix direction and affected responsibility: Completed in Developer Guide.
- Tests to add/update: None required for documentation correction.
- Documentation impact: Correction complete.
- Verification after fixing: Compared documented claims with source; live gateway claims remain qualified.

## Positive observations
- Spec and guide explicitly qualify probabilistic classification and fail-open behavior; reviewer output is not directly returned.

## Gaps and limitations
- This is a focused specialist review; no commands executing tests, build or live services were run. Other axes and final release readiness require their own assessments.
- Mocked request tests cannot establish live gateway compatibility, classifier recall, injection resistance or real latency.

## Manual checks for user
- Run authorized synthetic live gateway checks for model availability, tool support, reviewer classification and latency, and assess deployed workflow and fail-open risk.

## Conclusion
- Prior contract findings are fixed by inspection. Live acceptance remains unverified.
