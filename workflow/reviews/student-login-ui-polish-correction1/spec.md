# Specification and Contract Review

## Status
- Target: HEAD `455a4d2163088047b9db87f3d5c35378b58ea707` and worktree changes; tracked diff SHA-256 `2909b5f40c14837cc09ba429d873f456c8b474b618e67686645800a201d7807a`; untracked hashes in implementation evidence.
- Scope: assigned student/login frontend changes and affected contracts; specification axis only.
- Overall: PASS for this axis, subject to the limitations below.
- Independent human review: READY for this axis; other axes determine overall readiness.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Reported passed | Implementer reports `npm run build`; not independently rerun. |
| Tests | Reported passed | Implementer reports 18 files / 65 tests; not independently rerun. |
| Smoke/acceptance testing | Partial | Supplied correction evidence describes mocked browser checks; real assistive technology, production and live services remain untested. |
| Static analysis | Reported passed | Implementer reports frontend format and lint passed, with six warnings. |
| Packaging/resources | Reported passed | Implementer reports build passed with chunk-size warning. |
| Specification validation | Reviewed | Task acceptance criteria, frontend contracts, assigned changes and evidence; previous contract finding fixed below. |
| Documentation consistency | Reviewed with limitations | Changed frontend specs align with reviewed source and reported mock observations; no API/schema changes apparent. |

## Requirement and contract mapping
| Requirement | Assessment |
| --- | --- |
| AC-01 | Partial: correction evidence reports computed contrast for sampled rendered states; not exhaustive. |
| AC-02 | Source and mock evidence support deliberate draft, job, error and copy feedback; actual screen-reader speech remains unverified. |
| AC-03 | Source implements linked, named tabs and keyboard controls; implementer reports mock browser keyboard checks. |
| AC-04 | Source and reported 320, 768 and 1280 CSS-pixel checks cover sticky links, focus target and desktop split. |
| AC-05 | Source and mock evidence cover Python, hint context, initialization origins and history restoration; prior misleading save guidance corrected. |
| AC-06 | Source and reported mock browser checks cover pending and invalid login; existing session and redirect logic remains. |
| AC-07 | Source and reported mocked/browser checks cover success, failure, unavailable clipboard and attempt ordering. Actual speech remains unverified. |
| AC-08 | Source and reported mocked shell checks cover long names and navigation at three widths; reduced motion was emulated. Real devices remain untested. |
| AC-09 | Source and reported mock views support consistent presentation and preserved list semantics; visual judgments remain human review. |
| AC-10 | Source and reported mocked checks cover draft persistence, history, sent-time and hidden output, and selected-submission complexity. No live judge/provider evidence. |
| AC-11 | Implementer reports all four frontend checks passed after final changes; assigned changes remain within frontend/spec scope. This reviewer did not rerun checks. |
| Changed frontend specs | Reviewed: login progress, editor and hint context, linked tabs, copy feedback, navigation and reduced-motion descriptions correspond to source and supplied evidence. No general guide changes required by the assigned scope. |

## Next actions
- Implementation follow-up required: NO
- Edit documentation: NO
- Rerun code-review skill: NO for this axis unless relevant changes follow.
- Reason: The previous contract defect has been corrected; remaining limits are stated below.

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
- Automated and browser checks are implementer-reported, not independently repeated in this axis.
- Actual screen-reader speech, real-device behavior, production deployment, live judge/provider behavior and exhaustive contrast across all states are unverified. Mock tests do not establish live-service behavior.

## Manual checks for user
- Check announcements with assistive technology and assess representative layouts on real devices; confirm visual consistency and any remaining rendered contrast states.

## Conclusion
- The prior contract finding is fixed; no unresolved specification or contract finding was identified in the assigned scope.
