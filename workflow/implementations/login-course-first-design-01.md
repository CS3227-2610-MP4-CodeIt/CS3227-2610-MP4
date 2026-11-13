# Login course-first design implementation

- Status: BLOCKED — implementation exists; acceptance evidence is incomplete.
- Brief: [login-course-first-design](../tasks/login-course-first-design.md); subsequent user instruction approved the prototype C mark.
- Baseline: `88806f2`, branch `feat/login-design`, separate worktree. The original checkout's unrelated untracked files were left in place. The brief and prototype were copied, not removed; prototype SHA-256 matched the brief.
- Target: uncommitted worktree changes in `frontend/src/features/login/LoginPage.tsx` and `specs/frontend/frontend-login.md`, plus copied brief and prototype. No authentication logic changed.
- AC-01/02: local browser screenshots at 320, 700 and 1200 CSS-pixel viewport widths showed stacked/narrow and side-by-side/wider arrangements and the C mark; no exhaustive zoom or long-text inspection performed. The prototype uses a 760px breakpoint; implementation uses the project's 640px Tailwind breakpoint.
- AC-03: local browser keyboard entry and password visibility toggle worked, and the submit button enabled. Existing static-render tests cover pending and invalid feedback. A mocked 401 flow including clearing password and retaining username has not been exercised.
- AC-04: inspected source diff; session, login and role redirect logic is unchanged. Success and allowed/denied redirects for all roles were not exercised in this run.
- AC-05: browser accessibility tree exposes labels and password visibility; focus was visible on username. Contrast measurement, complete keyboard traversal, error/pending browser states and screen-reader execution remain unverified.
- AC-06: frontend `npm ci`, `npm run format:check`, `npm run lint`, `npm test`, `npm run build` succeeded; 18 test files and 65 tests passed. Lint emitted six existing Fast Refresh warnings; build emitted a large-chunk warning. npm reported 4 low and 2 moderate dependency vulnerabilities. `git diff --check` passed. No live service tested.
- Security scan: sandboxed `semgrep --version` failed due to empty trust anchors; escalated `semgrep --version && sh workflow/security/semgrep.sh /private/tmp/login-design-semgrep.json` succeeded with Semgrep 1.170.0, 225 rules, 119 files (75 TS, 44 Python); two pre-existing wildcard CORS findings in backend and executor, no parser errors. Scan covers tracked files only and is not proof of runtime security.
- First edit attempt failed due to incorrect working-directory-relative path; corrected and formatted. No secret values copied or used.
