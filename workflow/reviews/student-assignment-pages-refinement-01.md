# Code Review Report

## Status
- Target: worktree diff on `feat/student-assignment-pages` relative to 88806f2, including the copied task and prototype.
- Scope: two student assignment pages, focused tests and student frontend spec.
- Overall: PASS
- Independent human review: READY, subject to the limitations below.

## Checks
| Area | Status | Evidence |
| --- | --- | --- |
| Compilation, packaging | Passed | `npm run build`; large chunk warning |
| Tests | Partial | `npm test`: 69 passed; query failure states and some date/data partitions not directly exercised |
| Smoke/acceptance | Partial | Mocked Chrome list/detail at 375, 768, 1440; no horizontal document overflow in tested scenario |
| Static analysis | Passed | `npm run format:check`, `npm run lint`; six existing warnings |
| Specification and documentation | Partial | Student spec updated for progress and explicit status; remaining acceptance scenarios unverified |
| Security | Limited | Query hooks and Markdown component retained; no authorization or API change; security scan not run |
| Code quality | Assessed | Page-local layout, existing query hooks and date helper; no shared primitives changed |

## Next actions
- Implementation follow-up required: YES, for missing verification.
- Edit documentation: NO, unless further findings require it.
- Rerun code review: AFTER FOLLOW-UP WORK.
- Reason: required browser accessibility and query-state evidence is incomplete.

## Agent handoff
- Follow-up required: YES
- Current state: implementation and partial tests complete; no acceptance or commits.
- Next responsible skill or human: implement-task, then one-agent code-review.
- Priority and finding: CR-assignment-pages-01.
- Exact files: `frontend/src/features/student/AssignmentPages.test.tsx` and both page components.
- Required investigation: exercise loading, retry, not-found, keyboard focus and accessible names; inspect remaining representative responsive/prototype scenarios and data partitions.
- Constraints: preserve API, roles, safe Markdown and unrelated work.
- Verification: rerun relevant frontend checks and record browser methods/results.
- Success: all acceptance criteria supported or any remaining limitation explicitly accepted.
- Documentation impact: none anticipated.
- Required next rerun: code-review on final target.
- Blocker: missing verification evidence, not a known functional failure.

## Findings
- `CR-assignment-pages-01` — [Medium] Acceptance evidence incomplete — Status: Open
- Category: verification.
- Location: `frontend/src/features/student/AssignmentPages.test.tsx`; task AC-04–06.
- Requirement: inspect responsive layout and keyboard/accessibility, and exercise query states.
- Evidence: implementation handoff records mocked populated browser checks and passing tests, but no keyboard/accessibility-tree or query error/retry/404 exercise.
- Expected / actual: complete acceptance evidence / partial evidence.
- Reproduction: compare test coverage and handoff against the task table.
- Impact: usability and failure-state regressions cannot be ruled out.
- Likely cause / confidence: verification not completed; high confidence.
- Fix direction: complete focused checks, then rerun review.
- Tests to add/update: query-state coverage where practical.
- Documentation impact: none anticipated.
- Verification after fixing: report exact outcomes and remaining limitations.

## Positive observations
- Existing query and Markdown components are reused; progress derives from actual question flags.
- Tests and build pass; tested responsive pages have no document overflow.

## Gaps and limitations
- Mocked browser checks do not establish live backend behavior or screen-reader speech. Security scan not run.

## Manual checks for user
- Keyboard focus, accessibility tree and remaining responsive/prototype comparisons have not been completed.

## Conclusion
- Self-review is incomplete and is not independent review. Do not proceed to logging/commit stage until follow-up and accepted review.

## Follow-up review — 13 November 2026

The same scoped worktree was re-reviewed after follow-up checks. `CR-assignment-pages-01` is **Fixed**: mocked Chrome exercised loading, retry recovery and 404; checked keyboard order and focus styles, named links/headings in the accessibility tree, and long-content layouts at 375, 768 and 1440 CSS pixels. One- and three-question and future-due tests were added. The approved prototype elements were compared to screenshots; the progress card follows questions on narrow screens, while the prototype puts it before them. No functional defect identified in that difference. The optional progress bar is absent and the excluded continue control is absent.

Final checks: format, lint, 71 tests, build and `git diff --check` passed. Lint and build have the warnings noted in the implementation record. Semgrep OSS 1.170.0 scanned 120 files with 225 rules and no parser errors; two pre-existing wildcard-CORS findings are outside this frontend change. The changed pages and test were scanned. Authentication, ownership, safe Markdown and API access remain on existing boundaries; no security boundary change was found in the scoped diff.

- Implementation follow-up required: NO.
- Edit documentation: NO; the student spec was updated.
- Rerun code review: NO unless the reviewed target changes.
- Manual limitations: browser data and authentication were mocked; no live backend, screen-reader speech or deployment was tested. Review is self-review, not independent verification.
- No remaining open findings. Earlier BLOCKED status and its handoff above describe the initial review, superseded by this follow-up.

## Commit preparation — later assignment-page edits

The assignment pages subsequently gained decorative progress bars and list progress badges. The user approved including them. Source review confirms that each bar uses the same solved and total counts as its adjacent text, is hidden from the accessibility tree, and guards the zero-total case; zero solved is not labelled not started. The earlier statement that no progress bar is present describes the earlier version only. Current-worktree frontend formatting, lint, 71 tests and build passed; these checks also included an unrelated `QuestionPage.tsx` edit that is excluded from the planned commits. The bars and badges were not separately inspected in a browser or tested against screen-reader speech. The review remains a self-review with that additional limitation.
