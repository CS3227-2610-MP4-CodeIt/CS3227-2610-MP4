# Student assignment pages implementation

- Status: BLOCKED pending acceptance evidence and review.
- Task: [student assignment pages refinement](../tasks/student-assignment-pages-refinement.md).
- Baseline: 88806f2 on newly created `feat/student-assignment-pages` worktree; task and prototype copied from original checkout, whose unrelated untracked work was left intact. Prototype SHA-256 matched the brief.
- Review target: worktree diff relative to 88806f2: the two student page components, `AssignmentPages.test.tsx`, student frontend spec, and copied task/prototype. No commits.
- AC-01–03: rendered list/detail, explicit statuses and counts; tests cover ordering, no due date, past due, zero/partial/complete and defensive empty progress, empty list, no description and links. Focused tests failed before implementation on absent new labels and summary, then passed.
- AC-04: mocked Chrome runs at 375, 768 and 1440 CSS pixels with long titles found no document overflow, rendered list/detail and navigated from list to detail. Screenshots inspected at 375 detail and 1440 list. Further layout, long unbroken content, and prototype comparison remain.
- AC-05: unchanged QueryView and Markdown; existing Markdown tests passed. Loading, retry, 404 and role access were not exercised on these pages.
- AC-06: source uses links and explicit text. Keyboard focus and accessibility-tree inspection remain unverified.
- AC-07: original checkout untouched; no shared style or primitive changed. Frontend checks below passed.

## Verification

From `frontend/`: `npm ci` succeeded (npm reported 4 low and 2 moderate dependency vulnerabilities); `npm run format:check`, `npm run lint`, `npm test` (19 files, 69 tests), and `npm run build` succeeded. Lint reported six fast-refresh warnings outside these changes; build warned about a large chunk. Initial sandboxed test failed because Vite could not write its temporary directory; escalated rerun ran. Initial browser attempt lacked the bundled Playwright browser; installed Chrome worked after correcting the mock route. Chrome data and authentication were mocked; no live backend was tested.

## Remaining

Exercise query error/retry, loading, 404, keyboard and accessibility tree, remaining responsive/prototype comparison and additional acceptance scenarios. Review is self-review, not independent verification. No human log approval, commit, push or deployment has occurred.

## Follow-up verification — 13 November 2026

- Status: IMPLEMENTED; CR-assignment-pages-01 follow-up performed. The Chrome checks below used mocked authentication and API responses; they do not establish live backend or screen-reader speech.
- Chrome headless with local Vite: observed list loading, server error and successful retry, and detail 404. At 375, 768 and 1440 CSS pixels, populated list/detail with long class, title and description rendered without document-level horizontal overflow; past-due closed text and mixed statuses were visible. Inspected screenshots of narrow list and intermediate detail against the approved prototype direction; stronger class headings, spaced rows, description, question statuses and text progress are present; the optional bar and excluded continue control are absent. The prototype's narrow progress card precedes content; implementation places it after questions in reading order.
- Keyboard Tab inspection reached list assignment and detail question links in reading order with computed `outline-style: auto`; Chrome accessibility tree exposed named question links and Questions/Your progress headings. No actual screen-reader speech was tested.
- Added outcome tests for one and three questions, future due date, order and counts. From `frontend/`, `npm run format:check`, `npm run lint`, `npm test` (19 files, 71 tests) and `npm run build` all passed; six existing fast-refresh lint warnings and build chunk-size warning remain. `git diff --check` passed.
- Root `sh workflow/security/semgrep.sh /tmp/student-assignment-semgrep.json`, Semgrep OSS 1.170.0, 225 community rules, exit 0, 120 files, approximately 100% parsed lines, no errors; changed components and test were scanned. Two pre-existing wildcard CORS findings at backend/app/main.py:67 and code-execution/app/main.py:62; no changed frontend findings. Sandboxed version check failed due to empty certificate trust anchors; the scan succeeded outside sandbox. Scanner coverage is limited to its configured targets and cannot establish authorization or runtime behavior.
- Browser script initially failed on an assertion comparing trimmed accessible text to an untrimmed fixture; corrected and reran successfully. Initial sandboxed Chrome launch failed; rerun outside sandbox succeeded.

## Commit preparation — later assignment-page edits

The current assignment pages now include a decorative progress bar and progress badges added after the prior review. The user approved including these edits in the feature commit. The bar uses the displayed solved/total values and is hidden from assistive technology; adjacent text supplies the count. The list only labels partial solved work as in progress and all solved work as completed, and does not label zero solved as unstarted. The earlier sentence saying the optional bar is absent applies only to the previously reviewed version. On the current worktree, `npm run format:check`, `npm run lint`, `npm test` (71 passed) and `npm run build` passed, with the existing warnings recorded above. The separate `QuestionPage.tsx` change is excluded from the planned commits.
