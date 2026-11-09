# Security Boundary Review

## Status
- Target: HEAD `07ba2c4ca8963133d431359cb04f65ab724e840e` plus 16 task paths, supplied fingerprint `8652ec0b2f82a71e5d001f34b4e5265e0d046e62cb1cb244f93c3a01ca1334f6`.
- Scope: Student complexity authorization, ownership, job isolation, model input/output and resource boundaries; review only.
- Overall: FINDINGS — no security defect identified, but applicable live and revocation timing evidence is incomplete.
- Independent human review: READY for this axis with the stated limitations; aggregate readiness is a separate decision.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Not assessed | Outside this axis. |
| Tests | Passed, limited | `cd backend && .venv/bin/pytest tests/test_student.py -q -k complexity`: 6 passed, 25 deselected; mocked model. |
| Smoke/acceptance testing | Partial | Supplied integrated Chromium evidence exercises the real backend and fake provider, including saved-code and hidden-data checks; no live provider or in-flight membership revocation. |
| Static analysis | Partial | `sh workflow/security/semgrep.sh /tmp/codeit-security-run4.json`, exit 0; coverage and findings below. |
| Packaging/resources | Not assessed | Outside this axis. |
| Specification validation | Partial | Task and security matrix rows AUTH-04, DATA-01, JOB-01, AI-01, AI-02 and AI-04 inspected; provider behavior remains unverified. |
| Documentation consistency | Not assessed | Outside this axis. |

## Next actions
- Implementation follow-up required: NO.
- Edit documentation: NO.
- Rerun code-review skill: NO unless relevant changes or additional evidence require reassessment.
- Reason: No introduced security defect identified; limits below remain.

## Agent handoff
- Follow-up required: NO for identified defects; carry limitations into aggregate review.
- Current implementation/review state: Admission and reads enforce student membership and ownership; code-only model input and bounded structured output inspected.
- Next responsible skill or human: Aggregate reviewer; deployment owner for release-specific checks.
- Priority and finding addressed: No open SB findings.
- Exact files and line locations: `backend/app/routers/student.py:247`, `backend/app/routers/jobs.py:22`, `backend/app/ai/complexity.py:22`.
- Required change or investigation: If release assurance requires it, exercise in-flight membership revocation and approved benign/adversarial live provider probes with disposable data.
- Constraints and out-of-scope work: No production access, live model call or product edits.
- Verification commands: `cd backend && .venv/bin/pytest tests/test_student.py -q -k complexity`; `sh workflow/security/semgrep.sh /tmp/codeit-security-run4.json`.
- Manual checks: Release-specific in-flight revocation and live provider probes, if required.
- Success criteria: Revoked users cannot retrieve protected results; provider probes respect intended boundaries.
- Documentation impact: None identified.
- Required next rerun: Reassess after relevant changes.
- Blocker or decision needed: None for source assessment.

## Findings
No findings.

## Positive observations
- Student role, current assignment membership, question inclusion and submission ownership gate both routes; generic job reads recheck the same admission. Submission rows require a final verdict; pending jobs do not themselves create submission rows. Denial and concurrency tests pass with mocked dependencies.
- Stored code is scanned and wrapped as untrusted input; the model receives code only, with no tools, hidden tests or reference solution. Canary, total and field bounds and strict schema guard output; job work is timeout-bounded and deduplicated per owner and submission.
- Supplied integrated browser evidence reports the real backend with a fake provider checked saved snapshots and exclusion of draft, hidden markers and tools. It is not evidence of live model compliance.

## Gaps and limitations
- HEAD independently verified; the supplied ordered fingerprint was not independently reproduced because its ordering was not supplied. The review uses the 16 task paths named in the implementation handoffs.
- Semgrep 1.170.0 OSS ran on 9 November 2026 using mutable `p/python` and `p/typescript` registry packs: 225 rules, 111 scanned files (44 Python, 67 TypeScript), approximately 99.9% parsed; `backend/app/ai/complexity.py` was included. Two wildcard CORS matches in unchanged `backend/app/main.py:66` and `code-execution/app/main.py:62` are existing tracked WEB-01/EXEC-01 risks, not introduced here. Partial parsing at `backend/app/clients/llm.py:122` limits coverage. Python tests, specifications and configuration are outside configured roots; normal ignore filters apply. The scan cannot establish runtime authorization or prompt-injection resistance.
- Membership removal after admission and before completion, live provider behavior and deployed configuration remain unverified. No secrets or private payloads were printed.

## Manual checks for user
- If needed for release, use disposable data to verify access revocation during an in-flight job and run authorized benign/adversarial live-provider checks.

## Conclusion
No introduced security finding was identified within the inspected boundaries; mocked and static evidence has the limits above.
