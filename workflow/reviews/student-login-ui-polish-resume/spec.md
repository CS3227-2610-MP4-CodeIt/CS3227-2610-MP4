# Specification and Contract Review

## Status
- Target: HEAD `455a4d2163088047b9db87f3d5c35378b58ea707` plus assigned worktree changes; supplied tracked diff SHA-256 `88225dada7eabf61ca65c6f22dd4794542616b16e9a2de9e70dc37eef966f7bc` and untracked hashes in implementation evidence.
- Scope: assigned student/login UI changes and affected frontend contracts; specification/contract axis only.
- Overall: FINDINGS
- Independent human review: READY, subject to the finding and explicit acceptance evidence gaps below; no Blocker/High finding identified on this axis.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Not independently run | Implementation handoff reports frontend build passed. |
| Tests | Not independently run | Handoff reports 16 files / 61 tests passed; mocked and static tests have stated limits. |
| Smoke/acceptance testing | Incomplete | Handoff reports mock-backed Firefox scenarios; several viewport, shell and accessibility scenarios remain unverified. |
| Static analysis | Not independently run | Handoff reports format and lint passed with warnings. |
| Packaging/resources | Not independently run | Handoff reports frontend build passed with chunk-size warning. |
| Specification validation | Finding | Task acceptance criteria, changed source, affected specs, assignment brief and implementation evidence inspected; see mapping and SC-01. |
| Documentation consistency | Incomplete | Changed frontend specs inspected against source; responsive and spoken feedback claims require further verification. No API or schema changes apparent in assigned diff. |

## Requirement and contract mapping
| Requirement | Assessment and evidence |
| --- | --- |
| AC-01 contrast | Not verifiable: darker metadata is present, but actual rendered combinations have not all been measured. |
| AC-02 feedback | Incomplete: status and alert roles exist; no screen-reader speech check, and see SC-01 for contradictory draft feedback. |
| AC-03 result tabs | Verified at source and partially in mock browser: named, linked tabs/panels and keyboard handlers exist; handoff reports arrow, Home, End and Tab checks. |
| AC-04 narrow shortcuts | Partially verified: sticky navigation, focusable anchors and scroll offsets are present; handoff reports a zoomed mock workspace, without exact viewport or all target widths. |
| AC-05 editor/hint context | Finding: Python, hint context and origin selection are implemented; unconditional device-save claim contradicts storage failure state (SC-01). Empty/error origins were not checked in browser. |
| AC-06 login | Partially verified: source and reported mock browser cover invalid and pending states; role redirect source retained. |
| AC-07 clipboard | Partially verified: source and mocked tests cover success/failure/unavailable and guidance; browser failure rendering unverified. |
| AC-08 shared layout/motion | Incomplete: wrapping and reduced-motion classes exist; narrow long names, role shells and reduced-motion rendering remain unverified. |
| AC-09 visual consistency and data | Incomplete: source preserves grouping and ordering and supplies empty guidance; representative rendered visual and empty-state checks remain. |
| AC-10 persistence/privacy/history/complexity | Partially verified: draft selection preserved in source and mock browser reports history confirmation and reload; no live judge/provider verification. No changed request, auth or hidden-test contract identified. |
| AC-11 checks/scope | Automated checks reported passed by implementer; acceptance browser coverage remains incomplete. Assigned diff stays within stated frontend/spec scope. |
| Changed frontend specs | Source generally matches login, tab, hint and shared feedback descriptions. Narrow navigation and announcements remain subject to the evidence gaps above; no unrelated guide change required by this task. |

## Next actions
- Implementation follow-up required: YES
- Edit documentation: NO
- Rerun code-review skill: AFTER FOLLOW-UP WORK
- Reason: the editor's unconditional save claim contradicts the supported storage failure state.

## Agent handoff
- Follow-up required: YES
- Current implementation/review state: Independent contract review found one open Medium issue; other acceptance limitations are recorded above.
- Next responsible skill or human: implement-task, followed by code review and human acceptance.
- Priority and finding addressed: Medium, SC-student-login-01.
- Exact files and line locations: `frontend/src/features/student/QuestionPage.tsx:173`.
- Required change or investigation: Make the save description conditional or accurately describe attempted device-local persistence without implying success when storage is unavailable.
- Constraints and out-of-scope work: Preserve draft precedence, local storage behavior and submit semantics; no backend or API change.
- Verification commands: relevant focused frontend test, then applicable frontend checks per README.
- Manual checks: Simulate unavailable local storage, edit code, and confirm the visible guidance and save status agree; perform remaining responsive and accessibility checks listed below.
- Success criteria: Storage failure cannot coexist with an unconditional claim that edits are saved; successful local draft and submission guidance remain clear.
- Documentation impact: No spec change needed if implementation is aligned with the existing storage exception.
- Required next rerun: Review affected code and acceptance evidence after follow-up.
- Blocker or decision needed: None identified.

## Findings
- `SC-student-login-01` — [Medium] Editor promises local saves even when storage fails — Status: Open
- Category: Acceptance and persistence contract.
- Location: `frontend/src/features/student/QuestionPage.tsx:173`; `frontend/src/features/student/useDraftSaver.ts:23`; `specs/frontend/frontend-student.md:18`.
- Requirement: AC-05 requires truthful editor context; the student contract explicitly allows local storage to be full or unavailable and says drafts are not guaranteed.
- Evidence: The editor always says “Edits are saved on this device”, while the saver reports `unavailable` when its write fails and the adjacent status says the draft could not be saved.
- Expected / actual: Guidance should describe local saving accurately even on failure; instead it simultaneously asserts saving succeeded and failed.
- Reproduction or inspection path: Deny or exhaust local storage, edit the editor, and wait for the debounced save; compare origin guidance with draft status.
- Impact: A student can misunderstand whether their work will survive navigation or reload, risking lost work.
- Likely cause / confidence: Static instructional text ignores the saver state; high confidence from source.
- Fix direction and affected responsibility: Qualify the general description or vary it with save state, preserving local draft behavior.
- Tests to add/update: Cover the unavailable state and resulting user-facing guidance at a meaningful component boundary.
- Documentation impact: Existing storage exception is accurate; no documentation change required.
- Verification after fixing: Exercise failed and successful local saves and rerun relevant frontend checks.

## Positive observations
- Initial source and code are selected together without changing the existing draft-first precedence.
- Result tab relationships, selection controls, keyboard handlers and action-triggered tab selection are represented in source.

## Gaps and limitations
- This is a source and supplied-evidence review; checks and browser scenarios were not independently rerun.
- Actual screen-reader speech, precise viewport coverage, long account text and teacher/admin shells, browser clipboard failure, and browser empty/error origin states remain unverified in supplied evidence.
- No live judge or AI calls were made; mocked execution cannot establish deployed behavior.

## Manual checks for user
- Check workspace at narrow, intermediate and laptop widths with long content and long account text across student, teacher and admin shells; verify destinations are reachable and unobscured.
- Check pending/error, draft/job/reconnect/copy announcements with assistive technology, reduced-motion loading, and clipboard rejection rendering.
- Check empty/error initial code and unavailable local storage, plus the corrected save guidance.

## Conclusion
- One specification/acceptance finding requires implementation follow-up; remaining incomplete acceptance evidence should be completed or explicitly accepted by the human reviewer.
