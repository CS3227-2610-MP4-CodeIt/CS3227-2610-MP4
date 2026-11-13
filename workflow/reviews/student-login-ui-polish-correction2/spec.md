# Specification and Contract Review

## Status
- Target: HEAD `455a4d2163088047b9db87f3d5c35378b58ea707` and worktree changes; tracked diff SHA-256 `2909b5f40c14837cc09ba429d873f456c8b474b618e67686645800a201d7807a`; untracked hashes in implementation evidence.
- Scope: assigned student/login frontend changes and affected contracts; specification axis only.
- Overall: BLOCKED for full acceptance on this axis: exhaustive rendered contrast remains unverified; no open contract defect identified.
- Independent human review: READY for this axis; other axes determine overall readiness.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Reported passed | Implementer reports `npm run build`; not independently rerun. |
| Tests | Reported passed | Implementer reports 18 files / 65 tests; not independently rerun. |
| Smoke/acceptance testing | Partial | Correction-2 evidence reports additional mock browser checks of empty/populated student screens, reconnect and job transitions, and representative contrast. Real assistive technology and real devices remain untested. |
| Static analysis | Reported passed | Implementer reports frontend format and lint passed, with six warnings. |
| Packaging/resources | Reported passed | Implementer reports build passed with chunk-size warning. |
| Specification validation | Reviewed | Task acceptance criteria, frontend contracts, assigned changes and evidence; previous contract finding fixed below. |
| Documentation consistency | Reviewed with limitations | Changed frontend specs align with reviewed source and reported mock observations; no API/schema changes apparent. |

## Requirement and contract mapping
| Requirement | Assessment |
| --- | --- |
| AC-01 | Incomplete: correction-2 reports computed contrast in empty/populated lists, assignment detail, workspace job states, reconnect and invalid login; measured samples meet 4.5:1. Translucent composition, all hover/focus and other states remain unverified. |
| AC-02 | Verified at DOM/source level with limits: correction-2 reports reconnect and job status transitions; prior evidence covers draft, login and copy. Actual screen-reader speech remains unverified. |
| AC-03 | Source implements linked, named tabs and keyboard controls; implementer reports mock browser keyboard checks. |
| AC-04 | Source and reported 320, 768 and 1280 CSS-pixel checks cover sticky links, focus target and desktop split. |
| AC-05 | Source and mock evidence cover Python, hint context, initialization origins and history restoration; prior misleading save guidance corrected. |
| AC-06 | Source and reported mock browser checks cover pending and invalid login; existing session and redirect logic remains. |
| AC-07 | Source and reported mocked/browser checks cover success, failure, unavailable clipboard and attempt ordering. Actual speech remains unverified. |
| AC-08 | Source and reported mocked shell checks cover long names and navigation at three widths; reduced motion was emulated. Real devices remain untested. |
| AC-09 | Verified with limits: correction-2 reports empty and populated student list, correct 0 / 1 count and assignment detail at 768 CSS pixels; earlier evidence covers other workspace widths. Real-device and visual judgments remain human review. |
| AC-10 | Source and reported mocked checks cover draft persistence, history, sent-time and hidden output, and selected-submission complexity. No live judge/provider evidence. |
| AC-11 | Prior verification reviewer independently reported all four frontend checks passed on the identical target; correction-2 reports no source changes and a further `git diff --check` pass. This reviewer did not rerun checks. Contrast coverage remains incomplete as recorded under AC-01. |
| Changed frontend specs | Reviewed: login progress, editor and hint context, linked tabs, copy feedback, navigation and reduced-motion descriptions correspond to source and supplied evidence. No general guide changes required by the assigned scope. |

## Next actions
- Implementation follow-up required: NO
- Edit documentation: NO
- Rerun code-review skill: NO for this axis unless relevant changes follow.
- Reason: The previous contract defect remains corrected. No code defect was found; incomplete contrast coverage and other limits are stated below for the verification reviewer and human.

## Agent handoff
- Follow-up required: NO for this axis.
- Current implementation/review state: Previous contract finding fixed; no open contract findings identified.
- Next responsible skill or human: Aggregator and independent human reviewer.
- Priority and finding addressed: `SC-student-login-01`, Medium, fixed.
- Exact files and line locations: `frontend/src/features/student/DraftFeedback.tsx:24` and `frontend/src/features/student/DraftFeedback.test.tsx:5`.
- Required change or investigation: None on this axis.
- Constraints and out-of-scope work: Preserve local draft and submission behavior; no backend changes requested.
- Verification commands: Implementer reports focused draft tests and all four frontend checks passed; not independently rerun.
- Manual checks: Assistive-technology announcements and real-device presentation remain appropriate human checks.
- Success criteria: Qualified guidance and actual save status agree when storage is unavailable.
- Documentation impact: None; existing storage exception remains accurate.
- Required next rerun: Only after relevant changes.
- Blocker or decision needed: None on this axis.

## Findings
- `SC-student-login-01` — [Medium] Editor promises local saves even when storage fails — Status: Fixed
- Category: Acceptance and persistence contract.
- Location: `frontend/src/features/student/DraftFeedback.tsx:24`; `frontend/src/features/student/DraftFeedback.test.tsx:5`.
- Requirement: AC-05 requires truthful editor context; student contract permits unavailable local storage.
- Evidence: Guidance now qualifies device drafts with “when available”; the unavailable status explicitly reports failure. Static component tests cover unavailable and saved states; implementer reports a browser check with forced write failure.
- Expected / actual: Failure must not coexist with an unconditional save promise; source now qualifies the claim and displays the failure status.
- Reproduction or inspection path: Inspect the guidance and status components or force storage writes to fail and edit the code.
- Impact: Prior wording could mislead students about persistence; corrected wording and failure status address that risk.
- Likely cause / confidence: Previously unconditional guidance; high confidence in the source correction, with supplied mock browser evidence.
- Fix direction and affected responsibility: Completed in draft feedback components.
- Tests to add/update: Existing focused tests cover saved and unavailable wording.
- Documentation impact: None; the existing storage exception remains accurate.
- Verification after fixing: Implementer reports focused tests and forced-failure browser observation; this reviewer inspected source and evidence, without independent execution.

## Positive observations
- Initial editor content and origin are selected together, preserving draft-first precedence.
- Result tabs expose linked panels and keyboard navigation while action selection remains supported.

## Gaps and limitations
- The prior verification reviewer independently ran the four frontend checks on this identical target. Browser observations are implementer-reported and were not independently repeated in this axis; the correction-2 browser harness is ephemeral.
- Actual screen-reader speech, real-device behavior, production deployment, live judge/provider behavior and exhaustive contrast across all states are unverified. Mock tests do not establish live-service behavior.

## Manual checks for user
- Check announcements with assistive technology and assess representative layouts on real devices; inspect remaining meaningful contrast combinations, including translucent, hover and focus states.

## Conclusion
- The prior contract finding remains fixed; full acceptance is limited by unverified rendered contrast states.
