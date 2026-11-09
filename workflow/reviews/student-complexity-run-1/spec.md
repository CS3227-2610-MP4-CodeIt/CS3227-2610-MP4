# Specification and Contract Review

## Status
- Target: HEAD `07ba2c4ca8963133d431359cb04f65ab724e840e` plus assigned task changes; supplied aggregate SHA-256 `e7de8a56c3322f41a107d266c177252b4318adeb6252d8b2232d52b972d1538e` (not independently recomputed).
- Scope: specification and contract axis for the assigned complexity analysis change, task brief and prototype option 3.
- Overall: FINDINGS
- Independent human review: READY, subject to the documentation finding and limitations below.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation, tests, static analysis, packaging | Not independently run | Outside this specialist axis; implementation handoff reports passing checks. |
| Smoke/acceptance testing | Partially verified | Handoff reports mocked browser and backend checks; no live model or deployment check. |
| Specification validation | Incomplete | Task criteria mapped below; backend reference contains stale entries. |
| Documentation consistency | Incomplete | See SC-complexity-1. |

## Requirement mapping
| Requirement | Assessment and evidence |
| --- | --- |
| Completed own submission snapshot; accepted and non-accepted | Verified by source: `student.py` retrieves the owned submission's stored code; `judging.py` creates submissions after judging. Handoff reports mocked non-accepted case and browser snapshot check. |
| Big O time, auxiliary space, explanation and caveats | Verified as contract and presentation: `complexity.py` prompts for these and validates bounded nonempty fields; `QuestionPage.tsx` displays them. Semantic correctness of arbitrary model output is not verifiable statically. |
| Existing workspace, selected submission context, states and isolation | Verified by source and mocked browser evidence in handoff; browser in-progress state not separately exercised. |
| Membership, role, ownership, question and generic job read | Verified by source inspection and focused test evidence reported in handoff. Submission records are created after the judge returns rather than representing pending submissions. |
| Code limits, no execution, no hidden data or tools | Verified by source inspection: request uses stored code, `CodeIn`, and scan; handler sends only wrapped code with no tools. Live service behavior not checked. |
| Focused injection, output validation, access, deduplication and benign cases | Handoff reports mocked checks, including concurrent complexity requests. Tests not independently rerun. |
| Backend/frontend specs | Incomplete: appended sections describe the new flow but existing backend contract entries remain inaccurate or incomplete; see finding. |

## Next actions
- Implementation follow-up required: NO
- Edit documentation: YES
- Rerun code-review skill: AFTER FOLLOW-UP WORK
- Reason: synchronize the existing backend reference with the new contract and narrow migration behavior.

## Agent handoff
- Follow-up required: YES
- Current implementation/review state: Feature source and task evidence reviewed; one documentation finding open.
- Next responsible skill or human: Documentation implementer.
- Priority and finding addressed: Medium, SC-complexity-1.
- Exact files and line locations: `specs/backend-spec.md:225`, `:245`, `:269`, `:816`.
- Required change or investigation: Integrate complexity endpoints and job key into their reference tables, qualify generic job read authorization, and describe the specific jobs constraint upgrade without claiming general migrations exist.
- Constraints and out-of-scope work: Preserve approved contract and distinguish this narrow upgrade from a general migration system.
- Verification commands: Inspect the updated reference against `backend/app/routers/jobs.py`, `backend/app/routers/student.py`, and `backend/app/db.py`; run `git diff --check`.
- Manual checks: Confirm browser in-progress state and, when available, live model/deployed behavior.
- Success criteria: No contradictory or incomplete statements in affected backend reference sections.
- Documentation impact: Backend specification only.
- Required next rerun: Review the updated documentation.
- Blocker or decision needed: None.

## Findings
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

## Positive observations
- The selected-submission section follows prototype option 3 and keys analysis by submission ID.
- The model prompt requests auxiliary space and uncertainty; the schema bounds each output field and rejects extra fields.

## Gaps and limitations
- This review did not independently run checks or recompute the supplied aggregate hash. Test results are attributed to the implementation handoff.
- Mocked checks do not establish live SoCLaaS or deployed integration behavior.

## Manual checks for user
- Exercise the in-progress state in a browser and verify live model/deployment integration when available.

## Conclusion
- Contract implementation appears aligned with the approved task on the reviewed axis; the backend reference needs reconciliation before the documentation is consistent.
