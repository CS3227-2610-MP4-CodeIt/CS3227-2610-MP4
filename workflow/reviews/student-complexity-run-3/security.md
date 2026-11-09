# Security Boundary Review

## Status
- Target: HEAD `07ba2c4ca8963133d431359cb04f65ab724e840e` plus 16 task paths, supplied fingerprint `8652ec0b2f82a71e5d001f34b4e5265e0d046e62cb1cb244f93c3a01ca1334f6`.
- Scope: Complexity analysis authorization, submitted-code/model boundary, job isolation and related security configuration; review only.
- Overall: FINDINGS (no security defect identified; applicable live and revocation timing evidence remains incomplete).
- Independent human review: READY subject to the limitations below; final readiness is for the aggregate review.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Not assessed | Outside this specialist axis. |
| Tests | Passed, limited | `backend/.venv/bin/pytest tests/test_student.py -q -k complexity`: 6 passed, 25 deselected; mocked model. |
| Smoke/acceptance testing | Partial | Source and focused mocked tests inspected; live model, deployed access and in-flight membership revocation not established. |
| Static analysis | Partial | `sh workflow/security/semgrep.sh /tmp/codeit-security-run3.json`, exit 0; details below. |
| Packaging/resources | Not assessed | Outside this specialist axis. |
| Specification validation | Partial | Task acceptance and affected security matrix rows inspected; no live-provider assurance. |
| Documentation consistency | Not assessed | Outside this specialist axis. |

## Next actions
- Implementation follow-up required: NO.
- Edit documentation: NO.
- Rerun code-review skill: NO, unless relevant changes or additional evidence require reassessment.
- Reason: No introduced security defect identified; existing evidence limitations remain.

## Agent handoff
- Follow-up required: NO for identified defects; aggregate reviewer should carry limitations.
- Current implementation/review state: Authenticated owner and membership checks precede job admission and retrieval; code-only prompt and bounded structured response inspected.
- Next responsible skill or human: Aggregate reviewer; deployment owner for any release-specific checks.
- Priority and finding addressed: No open SB findings.
- Exact files and line locations: `backend/app/routers/student.py:247`, `backend/app/routers/jobs.py:22`, `backend/app/ai/complexity.py:22`.
- Required change or investigation: If release assurance requires it, exercise access revocation during an in-flight request and live gateway behavior with approved disposable data.
- Constraints and out-of-scope work: No production access or live model call performed. No new tests or source edits.
- Verification commands: `cd backend && .venv/bin/pytest tests/test_student.py -q -k complexity`; `sh workflow/security/semgrep.sh /tmp/codeit-security-run3.json`.
- Manual checks: Check deployed authorization revocation and live gateway behavior if required for release.
- Success criteria: Revoked access cannot retrieve protected results; approved benign and adversarial probes respect intended controls.
- Documentation impact: None identified.
- Required next rerun: Aggregate review; reassess after relevant changes.
- Blocker or decision needed: None for this specialist's source assessment.

## Findings
No findings.

## Positive observations
- Student role, assignment membership, question inclusion and submission ownership gate POST and GET. Generic job reads also recheck admission. Completed submissions have a non-null final verdict by schema; pending jobs do not create submission rows.
- Code is fetched from the stored submission; model receives wrapped code only, no tools or hidden test context. Injection scan, canary check, bounded response and strict result schema are applied. Jobs are owner-scoped and deduplicated. SSE publishes only owner-scoped job identifiers, kind and target key, not result contents.
- Focused tests passed for mocked access, payload and output guard cases; they do not establish semantic model compliance.

## Gaps and limitations
- HEAD was independently verified. The supplied fingerprint is recorded but not independently reproduced: the ordering used for its ordered per-file hash listing was not supplied; a different handoff-order calculation did not match. Scope is the 16 paths listed in the implementation handoffs.
- Semgrep 1.170.0 OSS, configured mutable `p/python` and `p/typescript` registry packs, 225 rules, 111 scanned files (44 Python, 67 TypeScript), approximately 99.9% parsed. `backend/app/ai/complexity.py` was included. Two wildcard CORS matches in unchanged `backend/app/main.py:66` and `code-execution/app/main.py:62` are existing tracked WEB-01/EXEC-01 risks, not introduced by this task. Partial parsing at `backend/app/clients/llm.py:122` limits coverage. Python tests, specs and configuration lie outside configured roots; normal ignore filters apply. Results cannot establish runtime authorization or injection resistance. The script completed despite an earlier standalone version invocation failing due to empty trust anchors.
- Planned matrix rows AUTH-04, DATA-01, JOB-01, AI-01 and AI-02 and task-specific AI-04 were inspected. Membership removal after admission and before completion, live provider behavior and deployed configuration remain unverified. No secrets or private payloads were printed in this review.

## Manual checks for user
- If needed for release, with disposable data verify revocation during an in-flight job and perform authorized benign/adversarial live-model checks. No live call is required by the task's automated verification path.

## Conclusion
No introduced security finding was identified within the inspected boundaries; static and mocked evidence has the limits above.
