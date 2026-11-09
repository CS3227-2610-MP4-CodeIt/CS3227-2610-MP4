# Code Review Report

## Status
- Target: current scoped worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`.
- Scope: backend hint changes and tests, `specs/backend-spec.md`, and `docs/DeveloperGuide.md`; unrelated work excluded.
- Overall: FAIL — security, specification and verification axes remain blocked by unavailable live evidence; packaging is also blocked. All five recorded findings are fixed.
- Independent human review: BLOCKED pending live evidence and assessment of residual risk.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Passed by verification reviewer | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync mypy app`, exit 0, 34 files. |
| Tests | Passed by verification reviewer | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync pytest -q`, 200 passed; external services mocked. |
| Smoke/acceptance testing | Partial / blocked | In-process API and persisted-job tests; live gateway, container and deployment not exercised. |
| Static analysis | Partial | Verification reviewer reports Ruff format and lint and root `git diff --check` passed; supplied Semgrep evidence has exclusions and unpinned registry rules. See security and verification axes. |
| Packaging/resources | Blocked | Verification reviewer: `backend/`, `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build --offline`, exit 2; cached setuptools >=84.2.1 unavailable. |
| Specification validation | Partial | Contract reviewer inspected AC-01–07; live service properties unverified. |
| Documentation consistency | Verified by inspection | Contract reviewer compared changed guide and spec with implementation. |

## Next actions
- Implementation follow-up required: NO based on confirmed findings; investigate live behavior and residual risk.
- Edit documentation: NO; record new evidence and limitations as appropriate.
- Rerun code-review skill: AFTER FOLLOW-UP WORK or relevant new evidence.
- Reason: No open findings; blocked live acceptance and packaging evidence remain.

## Agent handoff
- Follow-up required: BLOCKED for full verification.
- Current implementation/review state: Five prior findings fixed; quality axis passed; contract, security and verification axes blocked on evidence.
- Next responsible skill or human: AI and release owners, then independent human reviewer.
- Priority and finding addressed: Live acceptance and residual disclosure risk, and package build; no open finding.
- Exact files and line locations: `backend/app/ai/hints.py` reviewer and generator, `backend/app/ai/guards.py` spotlighting, and tests identified in the verification axis; precise additional lines not supplied.
- Required change or investigation: Obtain build dependency and repeat offline build; assess configured models, tool support, classifier behavior, latency, gateway and deployment using authorized synthetic data, and assess fail-open risk.
- Constraints and out-of-scope work: Preserve protected data, approved fail-open behavior and unrelated work; metered live calls require authorization per verification reviewer.
- Verification commands: From `backend/`, `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build --offline`; authorized synthetic live gateway probes (exact commands not supplied).
- Manual checks: Live model availability, adversarial classification, timeout, latency and deployed workflow using synthetic/disposable data.
- Success criteria: Successful packaging, recorded live/deployment outcomes and independent human assessment of residual risk.
- Documentation impact: No correction identified; record new evidence and limitations.
- Required next rerun: After relevant changes or new verification evidence.
- Blocker or decision needed: Cached build dependency and live gateway access/authorization; human residual-risk assessment.

## Findings
Five retained findings: `CQ-private-hint-reviewer-01` (Medium, Fixed), `SC-private-hint-1` (High, Fixed), `SC-private-hint-2` (Medium, Fixed), `VR-private-hint-01` (Medium, Fixed), and `VR-private-hint-02` (Medium, Fixed). Full finding fields, verification and evidence limits follow in roster order; no findings were merged.

## Positive observations
- Reviewers report lossless encoded reviewer input, strict verdict parsing, bounded deadlines and privacy-preserving diagnostics. Mocked integration coverage includes hostile content and persisted job outcomes.

## Gaps and limitations
- Live model, gateway, deployment, provider retention, semantic injection resistance and classifier recall remain unverified. Approved fail-open behavior retains disclosure risk; the small prior classifier sample is not a broad recall estimate.
- Offline packaging is blocked; Semgrep coverage and metadata are limited as described by the security reviewer. Specialist reviewers did not all independently execute checks. Aggregation did not rerun checks or review source.

## Manual checks for user
- AI owner: when authorized, use synthetic protected outputs and disposable data to check live model availability, tool support, classification, timeout and latency, and exercise the deployed workflow. Assess residual fail-open risk.

## Conclusion
- FAIL due to unresolved blocked axes, despite no open findings. Independent human review remains blocked pending evidence and risk assessment.

# Axis reports

## Code quality

# Code Quality Review Report

## Status
- Target: scoped worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`, including the untracked reviewer tests.
- Scope: changed backend hint, gateway client, settings, job runner and startup implementation, with associated tests and supplied correction evidence. This assessment covers code quality only.
- Overall: PASS on this axis; no open code-quality findings.
- Independent human review: READY on this axis, subject to the other review axes and limitations below.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Supplied evidence | Corrections report records backend mypy passing; not rerun by this reviewer. |
| Tests | Supplied evidence | Corrections report records 200 backend tests passing, including diagnostic and cancellation coverage; not rerun by this reviewer. |
| Smoke/acceptance testing | Partial | Supplied tests mock external services; no live gateway assessment on this axis. |
| Static analysis | Supplied evidence | Corrections report records Ruff format and lint passing; not rerun by this reviewer. |
| Packaging/resources | Unverified | Corrections report records offline build failure due to unavailable cached setuptools. |
| Specification validation | Outside axis | Assigned to contract reviewer. |
| Documentation consistency | Outside axis | Assigned to contract reviewer. |

## Next actions
- Implementation follow-up required: NO on this axis.
- Edit documentation: NO on this axis.
- Rerun code-review skill: NO on this axis unless relevant changes follow.
- Reason: The prior diagnostic defect is corrected; no further material maintainability defect was identified in the changed implementation areas.

## Agent handoff
- Follow-up required: NO on this axis.
- Current implementation/review state: Prior code-quality finding fixed by inspection and supplied test evidence.
- Next responsible skill or human: Consolidating reviewer and independent human reviewer.
- Priority and finding addressed: Medium `CQ-private-hint-reviewer-01`, fixed.
- Exact files and line locations: `backend/app/ai/hints.py:175`.
- Required change or investigation: None on this axis.
- Constraints and out-of-scope work: Preserve fail-open behavior, content-free diagnostics and cancellation semantics.
- Verification commands: Supplied corrections report records focused tests, full backend pytest, Ruff and mypy; this reviewer did not rerun them.
- Manual checks: Live model availability and operational behavior remain unverified.
- Success criteria: No open code-quality finding; other axes assessed independently.
- Documentation impact: None on this axis.
- Required next rerun: After relevant follow-up changes.
- Blocker or decision needed: None on this axis.

## Findings
- `CQ-private-hint-reviewer-01` — [Medium] Unexpected reviewer bugs are indistinguishable from expected fail-open failures — Status: Fixed
- Category: Error handling and operator diagnostics.
- Location: `backend/app/ai/hints.py:175`.
- Requirement: Distinguish unexpected implementation failures from expected reviewer failures without logging protected content, while preserving fail-open behavior and cancellation.
- Evidence: Expected `UserFacingError`, `TimeoutError` and `ValueError` produce a content-free warning; other `Exception` instances produce a distinct content-free error. Cancellation is not caught by these handlers. The corrections report records tests for both diagnostics and cancellation.
- Expected / actual: Unexpected failures are distinguishable from expected failures; the revised handlers do so while returning the guarded hint.
- Reproduction or inspection path: Inspect `_review_hint` exception handlers and supplied correction evidence.
- Impact: Operators can distinguish an unexpected failure from routine reviewer failures without exposing exception content.
- Likely cause / confidence: Previously shared broad handler; high confidence in the separation from source inspection.
- Fix direction and affected responsibility: Completed in reviewer error handling.
- Tests to add/update: Correction evidence reports distinct diagnostic and cancellation tests.
- Documentation impact: None.
- Verification after fixing: Source inspected; focused and full test and static check results are reported by the implementer, not independently rerun here.

## Positive observations
- The reviewer call is separated from generator tool handling and has explicit timeout and size limits. Strict parsing rejects duplicate keys and invalid verdict shapes.
- Job deadlines use the event-loop clock and the reviewer does not swallow cancellation.

## Gaps and limitations
- Code-quality assessment covers the changed hint, gateway, configuration, job and startup areas; security, contracts and test adequacy are separate review axes.
- Live gateway behavior, model quality, latency and packaging remain unverified; supplied tests mock external services.

## Manual checks for user
- When authorized, verify model availability and real gateway behavior with synthetic data; assess deployment separately.

## Conclusion
- The prior code-quality finding is fixed. No new material code-quality findings were identified.


## Specification and contracts

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


## Security boundaries

# Security Boundary Review

## Status
- Target: scoped worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`, following corrections.
- Scope: private hint reviewer, hidden answers, prompt boundary, gateway and deadline; unrelated work excluded.
- Overall: BLOCKED — no confirmed introduced security defect; live gateway and classifier behavior remain unverified.
- Independent human review: BLOCKED pending assessment of live behavior and residual disclosure risk.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Not independently run | Outside this axis; previous implementation evidence reports mypy passed. |
| Tests | Evidence inspected | Current tests cover lossless hostile tag content and job timeout/shutdown paths; not independently executed in this review. Previous report's 194 passing tests predate follow-up corrections. |
| Smoke/acceptance testing | Partial | Mocked request and job tests inspected; no live gateway or adversarial model test performed. |
| Static analysis | Partial | Supplied `/tmp/codeit-private-hint-followup-semgrep-final.json`: Semgrep 1.170.0, 112 scanned paths, no reported errors, two pre-existing wildcard CORS findings in backend and executor. Supplied evidence reports exit 0. Shared script uses OSS `p/python` and `p/typescript` Registry packs; exact downloaded rule snapshot/count and skipped candidate list were not supplied. Scanned paths include changed backend application files; tests, specs, configuration and other excluded paths are outside the scan. A local `semgrep --version` attempt failed due to empty system trust anchors; no new scan was claimed. Findings concern unchanged open CORS configuration and do not establish a new bypass. |
| Packaging/resources | Not assessed | Outside security axis; prior offline build was blocked by unavailable setuptools. |
| Specification validation | Inspected | Task AC-01–07 and current backend spec authorize reviewer-only hidden outputs and bounded fail-open behavior. |
| Documentation consistency | Inspected | Task and prior evidence disclose classifier and fail-open limitations. |

## Next actions
- Implementation follow-up required: NO
- Edit documentation: NO
- Rerun code-review skill: NO, unless relevant changes follow.
- Reason: No confirmed introduced security defect; live classifier and provider behavior remain unproven.

## Agent handoff
- Follow-up required: BLOCKED
- Current implementation/review state: Source and supplied scan inspected; live model and gateway behavior unverified.
- Next responsible skill or human: AI owner and independent human reviewer.
- Priority and finding addressed: Residual disclosure and prompt-injection risk; no finding assigned.
- Exact files and line locations: `backend/app/ai/hints.py` reviewer flow and `backend/app/ai/guards.py` spotlighting.
- Required change or investigation: Assess gateway availability, latency, retention and classifier behavior using synthetic protected values and adversarial inputs; assess approved fail-open risk.
- Constraints and out-of-scope work: Preserve approved fail-open policy and do not disclose private content in logs or responses.
- Verification commands: Project-authorized live synthetic probes; rerun configured Semgrep scan if matching complete scan metadata is needed.
- Manual checks: Verify live model availability, timeout behavior and adversarial classification with synthetic data.
- Success criteria: Live evidence and explicit human assessment of residual disclosure risk.
- Documentation impact: Record any new evidence and limitations.
- Required next rerun: After relevant changes or new evidence.
- Blocker or decision needed: Live gateway and model behavior were not established by the supplied evidence.

## Findings
No confirmed findings.

## Positive observations
- Generator tools select visible test cases only; the private tool-free reviewer receives hidden expected outputs but not hidden inputs. Reviewer output is parsed privately and never forwarded.
- JSON encoding escapes angle brackets before spotlighting, preserving tag-like candidate, context and output text when decoded without allowing literal closing tags to escape the envelope. The revised hostile-content test checks candidate and hidden-output round trips.
- Strict verdict parsing rejects duplicate or extra fields and non-booleans. Reviewer failures and canary leaks log content-free messages and follow explicitly approved fail-open behavior; cancellation propagates.
- Reviewer size and deadline limits avoid silent truncation and bound the call. Current tests exercise timeout, exhausted budget and shutdown in the job lifecycle.

## Gaps and limitations
- Spotlighting and JSON encoding preserve the data boundary syntactically; they cannot guarantee semantic instruction resistance by a model. A mistaken or manipulated valid verdict, as well as any approved fail-open path, can allow a leaking candidate. Supplied prior classifier evidence observed 7/9 bad examples caught; it is not a broad recall estimate.
- Provider retention, real model availability, live latency, gateway limits and production behavior were not verified. The reviewer and gateway receive hidden expected outputs by approved design.
- Authentication and ownership code was unchanged and was not independently exercised across all roles and states. Static scan exclusions and missing rule snapshot limit its conclusions.

## Manual checks for user
- AI owner: perform authorized live synthetic benign and hostile probes, verify model availability and deadline behavior, and assess residual risk before relying on the classifier.

## Conclusion
No confirmed introduced security finding. Live security behavior and residual fail-open disclosure risk remain for human assessment.


## Verification and evidence

# Verification Review Report

## Status
- Target: scoped worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`; HEAD confirmed at baseline. Scope: assigned backend implementation and tests, backend spec and Developer Guide; unrelated work excluded.
- Overall: BLOCKED — offline packaging and live-service evidence remain unavailable. No open verification findings.
- Independent human review: BLOCKED pending assessment of these limitations.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation/type checking | Passed | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync mypy app`, exit 0, 34 files. |
| Tests | Passed | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync pytest -q`, exit 0, 200 passed in 32.79s; external services mocked. |
| Smoke/acceptance | Partial / blocked | In-process API and persisted-job tests exercised; live gateway, container and deployment not exercised. Metered live calls require authorization. |
| Static analysis | Passed with scope limitations | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync ruff format --check .` and `ruff check .`, both exit 0; root `git diff --check` exit 0. Supplied `/tmp/codeit-private-hint-followup-semgrep-final.json` reports Semgrep 1.170.0, zero errors and 112 scanned files; correction evidence records 225 rules, four exclusions and two pre-existing CORS findings. Security review owns triage; scan does not cover excluded files and registry rules are not pinned. |
| Packaging/resources | Blocked | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build --offline`, exit 2; setuptools >=84.2.1 absent from cache. No installation attempted. |
| Specification validation | Partial | Task ACs compared with tests and implementation; live service properties remain unverified. |
| Documentation consistency | Not assessed | Assigned to contract review. |

## Acceptance evidence
- AC-01: Supported by generator guard, no-review-on-empty/canary and bounded-loop tests; mocked gateway.
- AC-02: Supported for default request model selection and startup without reviewer by mocked tests; overrides and unrelated feature selection inspected in source rather than exercised end to end.
- AC-03: Supported at mocked integration level: hostile tag-shaped candidate and hidden output round-trip, tool round requests, separate nonce, hidden input exclusion and private response/log checks; semantic resistance to hostile content remains unverified live.
- AC-04: Supported by strict parsing tests and four verdict combinations, including rejection through a job.
- AC-05: Supported at mocked unit and job levels for invalid verdict, canary, timeout and call errors with safe diagnostics; actual provider behavior unverified.
- AC-06: Supported at mocked integration level for timeout fail-open, exhausted budget and shutdown with persisted outcome, and unit-level cancellation and size limits. Live latency, input limits and model availability blocked/unverified.
- AC-07: Supported by mocked bounded-loop test asserting four generator calls and one reviewer call.

## Next actions
- Implementation follow-up required: NO, on this axis.
- Edit documentation: NO, on this axis.
- Rerun code review: after relevant changes or new evidence.
- Reason: prior coverage findings have been addressed; packaging and live-service limits need separate evidence and assessment.

## Agent handoff
- Follow-up required: BLOCKED for full verification.
- Current implementation/review state: 200 backend tests pass with mocked dependencies; both prior verification findings fixed.
- Next responsible skill or human: release/AI owner and independent reviewer.
- Priority and finding addressed: packaging and live validation limitations, no open finding.
- Exact files and line locations: `backend/tests/test_student.py` hostile content and persisted deadline tests; `backend/tests/test_hint_reviewer.py` failure and cancellation tests.
- Required change or investigation: run offline build once build dependency is available; assess model availability, latency and classifier behavior with authorized synthetic probes.
- Constraints and out-of-scope work: no metered live calls without authorization; preserve private data and approved fail-open behavior.
- Verification commands: from `backend/`, `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build --offline`; perform authorized synthetic live gateway checks.
- Manual checks: test real configured models and deployment workflow with disposable data.
- Success criteria: successful package build and recorded live/deployment outcomes, with residual risk assessed by human reviewer.
- Documentation impact: record any new evidence; documentation review belongs to contract axis.
- Required next rerun: after relevant changes or new verification evidence.
- Blocker or decision needed: cached build dependency and authorization/access for live verification.

## Findings
- `VR-private-hint-01` — [Medium] Hostile reviewer input and private-output boundaries lacked integration coverage — Status: Fixed
- Category: acceptance / security-boundary verification.
- Location: `backend/tests/test_student.py`, `test_hint_reviewer_hostile_content_is_lossless_and_private`.
- Requirement: AC-03 hostile content, separation, spotlighting and private output handling.
- Evidence: new test inspects each generator call, reviewer data round trips and nonce, excluded hidden input, and API/log absence of private reviewer response; full suite passed. Hostile question-context and fresh canary behavior remain less directly exercised, and mock testing cannot prove model compliance.
- Expected / actual: planned boundary regression coverage now substantially exercised; live behavior remains unverified.
- Reproduction or inspection path: inspect named integration test and run backend suite above.
- Impact: prior regression coverage gap reduced.
- Likely cause / confidence: follow-up added outcome assertions; high confidence.
- Fix direction and affected responsibility: completed by backend test owner.
- Tests to add/update: none required for this finding.
- Documentation impact: none on this axis.
- Verification after fixing: full suite, 200 passed.

- `VR-private-hint-02` — [Medium] Reviewer deadline was not verified through persisted job lifecycle — Status: Fixed
- Category: timeout / state-transition verification.
- Location: `backend/tests/test_student.py`, `test_hint_review_timeout_persists_fail_open`, `test_hint_review_skips_when_job_budget_exhausted`, and `test_hint_review_shutdown_persists_failed_job`.
- Requirement: AC-06 reviewer deadline, fail-open and effective cancellation.
- Evidence: tests exercise delayed reviewer, depleted budget and active-review shutdown through actual job lifecycle and assert outcomes; suite passed.
- Expected / actual: guarded hint persists after reviewer timeout or skip; shutdown persists failed job; tests demonstrate those outcomes.
- Reproduction or inspection path: inspect named tests and run backend suite above.
- Impact: prior composed-deadline coverage gap addressed.
- Likely cause / confidence: follow-up added integration cases; high confidence.
- Fix direction and affected responsibility: completed by backend test owner.
- Tests to add/update: none required for this finding.
- Documentation impact: none on this axis.
- Verification after fixing: full suite, 200 passed.

## Positive observations
- Four verdict combinations and invalid schemas, resource limits and safe failure diagnostics are covered.
- New shutdown test observes a failed persisted job while the reviewer is active.

## Gaps and limitations
- Mocked tests cannot establish live availability, gateway limits, latency, provider retention, classifier recall or semantic injection resistance. Prior small classifier evidence and approved fail-open behavior leave residual leakage risk.
- Offline package build remains blocked. Frontend and executor checks are not applicable to this backend-only change; browser/container/deployment behavior is not proven.

## Manual checks for user
- When explicitly authorized, use synthetic protected outputs and disposable data to test the configured models, reviewer behavior and latency, then exercise the deployed workflow. Assess residual fail-open risk.

## Conclusion
No open verification findings; packaging and live/deployment evidence remain blocked or unverified.
