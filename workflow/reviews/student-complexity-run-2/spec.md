# Specification and Contract Review

## Status
- Target: HEAD `07ba2c4ca8963133d431359cb04f65ab724e840e` plus assigned task changes, supplied fingerprint `7be3df64cfd9bab36470509ba9ecb72e019608104922861d40d94002d3028b6f` (not independently recomputed).
- Scope: Student complexity task, option 3 prototype, affected contracts and correction evidence.
- Overall: FINDINGS
- Independent human review: READY, subject to the documentation correction and limitations below.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Not assessed | Outside this axis; implementation handoff reports frontend build passed. |
| Tests | Not independently run | Implementation handoff reports backend and frontend suites passed with mocked external services. |
| Smoke/acceptance testing | Incomplete | Handoff reports mocked Chromium; real backend/browser and live model remain unverified. |
| Static analysis | Not independently run | Handoff reports Ruff, mypy, lint and Semgrep results. |
| Packaging/resources | Not independently run | Handoff reports offline backend build and frontend build passed. |
| Specification validation | Incomplete | Requirement mapping below; feature section is nested under out-of-scope. |
| Documentation consistency | Incomplete | See SC-complexity-1. |

## Requirement mapping
- Completed own submission and snapshot (criterion 1): verified by source: the submission-specific route loads stored code and the panel starts it using the selected submission ID; submission records represent completed verdicts. Pending-state denial cannot be directly demonstrated with the current schema.
- Big O, auxiliary space, explanation and caveats (criterion 2): verified as requested in the prompt and rendered from structured fields; actual model quality is not verifiable without a live call.
- Existing workspace and selected submission states (criterion 3): verified by source and reported mocked browser evidence; real integration and responsive presentation remain unverified.
- Membership, owner and question admission (criterion 4): verified by route inspection, including generic job reads; pending-state limitation above applies.
- Limits and model boundary (criterion 5): verified by source inspection and supplied evidence; model output is untrusted and no tools are supplied.
- Focused tests (criterion 6): correction handoff reports focused guard tests and successful guard-removal mutations; not independently rerun.
- Backend/frontend specifications (criterion 7): incomplete; new backend feature is placed under out-of-scope, as below. Route and kind tables, generic read exception and migration exception were corrected.

## Next actions
- Implementation follow-up required: NO
- Edit documentation: YES
- Rerun code-review skill: AFTER FOLLOW-UP WORK
- Reason: Correct the contradictory backend specification placement.

## Agent handoff
- Follow-up required: YES
- Current implementation/review state: Reference tables and migration exception were corrected; the feature description remains under the out-of-scope heading.
- Next responsible skill or human: Documentation implementer.
- Priority and finding addressed: Medium, SC-complexity-1.
- Exact files and line locations: `specs/backend-spec.md:235`, `specs/backend-spec.md:812`, `specs/backend-spec.md:821`.
- Required change or investigation: Move the complexity contract to the features-using-jobs section or another in-scope section and fix its cross-reference.
- Constraints and out-of-scope work: Preserve the documented implementation contract; no behavior change needed.
- Verification commands: Inspect heading hierarchy and cross-reference; `git diff --check`.
- Manual checks: Exercise real-backend browser states, submission switching, retry and responsive/keyboard presentation; live model and deployment as appropriate for release.
- Success criteria: Complexity is clearly in scope and the endpoint table points to its actual section.
- Documentation impact: Backend specification.
- Required next rerun: Review corrected documentation.
- Blocker or decision needed: None.

## Findings
- `SC-complexity-1` — [Medium] Complexity contract is nested under out-of-scope — Status: Open
- Category: Documentation / contract.
- Location: `specs/backend-spec.md:235`, `specs/backend-spec.md:812`, `specs/backend-spec.md:821`.
- Requirement: Acceptance criterion 7 requires an accurate backend specification of the new feature and its contract.
- Evidence: The new student endpoint table directs readers to §13, headed “Out of scope”; its complexity contract is a level-three subsection of that heading. The approved task and implementation establish complexity as in scope.
- Expected / actual: The feature contract should be in an in-scope section with a matching reference; it is currently described under out-of-scope.
- Reproduction or inspection path: Compare the endpoint row with the heading hierarchy and task acceptance criteria.
- Impact: Developers can interpret the implemented feature as excluded from the product or misunderstand its release status.
- Likely cause / confidence: Appended section after the existing final heading; high confidence.
- Fix direction and affected responsibility: Move the section into the job features area and update the cross-reference.
- Tests to add/update: None for this documentation correction.
- Documentation impact: Backend specification.
- Verification after fixing: Inspect heading hierarchy and endpoint link, then run `git diff --check`.

## Positive observations
- The prior missing endpoint and job-kind rows, generic-read exception, and migration exception are now present.
- Selected-submission placement follows option 3, and result fields explicitly label auxiliary space and assumptions.

## Gaps and limitations
- Source review only; no tests, browser checks or fingerprint calculation were independently executed. Handoff evidence is attributed to its executor.
- Mocked responses do not establish live model quality, real-backend browser integration or deployed behavior.

## Manual checks for user
- Verify loading, switching submissions during analysis, retry, existing workspace controls and responsive keyboard presentation with a local backend. Verify live model and deployment separately if release assurance requires them.

## Conclusion
- The earlier reference-table omissions are corrected, but the in-scope feature remains under the out-of-scope heading and needs a documentation correction.
