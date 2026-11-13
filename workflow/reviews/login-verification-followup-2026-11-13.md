# Login verification follow-up — 13 November 2026

## Scope and status

- Target: `feat/login-design`, HEAD `5a83b5a` as inspected before verification. Recheck the target before relying on these results if it has changed.
- Scope: remaining login acceptance evidence, using a separate local Vite instance and a synthetic local HTTP backend. No real accounts or production data used.
- Overall: BLOCKED. A role-safe `next` redirect did not reach the requested destination in two mocked browser scenarios. The cause and whether it also occurs against the real backend remain unverified.
- Independent human review: NOT READY. Additional role cases, responsive/error-state evidence and follow-up review remain.

## Checks

| Check | Result and evidence |
| --- | --- |
| Pending and invalid credentials | Browser against delayed mock: button disabled and showed “Logging in…”; 401 showed “Invalid username or password.” Username field remained populated and password field became empty in the accessibility tree. Mocked boundary, not real service. |
| Student valid `next` | Browser opened `/login?next=%2Fstudent%2Fassignments%2F7`, logged in as a mock student; final URL was `/student`, not the requested `/student/assignments/7`. Open finding below. |
| Teacher valid `next` | Browser opened `/login?next=%2Fteacher%2Fquestions`, logged in as a mock teacher; final URL was `/teacher/assignments`, not `/teacher/questions`. Open finding below. |
| Admin cross-role `next` | Mock admin logging in with student destination landed on `/admin/users`; the cross-role destination was not followed. This covers one cross-role case, not all roles and cases. |
| Already authenticated login | Mock admin visiting `/login` was redirected to `/admin/users`. |
| Format | `npm run format:check` from `frontend/`: passed. |
| Lint | `npm run lint` from `frontend/`: passed with six Fast Refresh warnings. |
| Tests | `npm test` from `frontend/`: 18 files, 66 tests passed. |
| Build | `npm run build` from `frontend/`: passed, with large chunk warning. |

## Finding

- **VR-login-followup-01 — valid same-role destination lost**
- Status: Open. Severity: High (approved login redirect contract is not observed in the two exercised cases).
- Location: login-to-router flow; exact cause not established.
- Expected: after a successful login, follow an allowed path under the authenticated role. Observed final URLs above instead resolve to role home pages.
- Reproduction: use a disposable mocked backend, open the exact login URLs above while logged out, then authenticate as the corresponding synthetic role. Check navigation sequence and component/auth state; confirm the result is not an artifact of the mock before changing implementation.
- Impact: users following a protected deep link may need to navigate to their intended page again. Cross-role rejection in one case remains intact; this observation does not establish an authorization bypass.
- Follow-up: investigate and fix if confirmed, add meaningful success and rejected-destination tests for all roles, and rerun browser verification and code review.

## Remaining evidence

Admin valid same-role destination and student/teacher denied destinations were not exercised. Zoom, long error text, contrast, full keyboard traversal, and responsive pending/error screenshots remain unverified in this follow-up. Earlier review recorded default-state views at 320, 700 and 1200 CSS pixels and focused username/password controls; that evidence predates the later feedback change. Screen-reader speech, real backend and deployment were not tested. The initial mock login page also showed no error until the 401 response, as expected. Browser automation did not provide a full recording or request trace; final URL is the observed navigation outcome.

Mock backend and mock Vite server were stopped after checking. Frontend test/build commands are local checks; they do not establish live backend behavior. No application code was edited during this review.

## Additional checks on the same date

- Mock admin valid `next=/admin/classes` landed at `/admin/users`. The valid same-role destination was not observed for any of the three roles tested.
- Mock student and teacher given `next=/admin/users` each landed at their own role home. Together with the earlier admin-to-student case, one cross-role case was exercised per role; the final destination was role-appropriate in all three. Because allowed destinations were also lost, this alone does not prove the reason for rejecting cross-role paths.
- The teacher valid-destination scenario was repeated using the earlier `feat/student-ui-polish` baseline, HEAD `88806f2`, against the same mock. It also landed at `/teacher/assignments`. This indicates the observed issue predates the new login design; the exact cause is still unconfirmed.
- Invalid-credential state was viewed at 320, 700 and 1200 CSS pixels. Document scroll width matched viewport width at all three sizes; the error remained visible at the checked viewports. Username → password → show-password keyboard focus was observed. These checks do not verify all keyboard paths, real 200% zoom, long error text, or measured contrast.
- The additional mocked servers were stopped and temporary browser tabs closed. Original login preview servers were not changed.

## Further browser verification — 13 November 2026

- Real local backend on `127.0.0.1:8000`, login frontend on `5180`: submitted a synthetic nonexistent username and invalid password. The UI showed the invalid-credentials message, retained the username and cleared the password. No real user account or successful login was used.
- Isolated mock backend: a deliberately long 400 response wrapped in the login form at a 320 CSS-pixel viewport with document scroll width 320. This demonstrates wrapping for the sample, not all possible messages; the card can grow for long errors.
- Keyboard traversal observed from username to password, password visibility toggle, and enabled login button; Space toggled the password visibility control and changed its accessible name/state.
- Calculated contrast from browser-computed OKLCH colors converted to linear sRGB: CodeIt wordmark against blue panel 6.26:1; headline against panel 16.37:1; guidance against white 7.56:1; labels against white 10.34:1; error against white 6.42:1; enabled button white text against blue 5.26:1. These are calculated values for the sampled rendered states, not an exhaustive contrast audit.
- Chrome browser zoom was set to 200% (Chrome UI confirmed), effective viewport 673 CSS px, document scroll width 673; the form was visible with ordinary vertical scrolling. Zoom was restored to 100% afterward. This check covers the default state, not every error or viewport combination.
- Actual screen-reader speech and successful login with real credentials were not tested. Mocked role `next` redirect discrepancy remains open. Mock servers and temporary tabs were stopped/closed.
