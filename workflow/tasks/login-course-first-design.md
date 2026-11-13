# login-course-first-design — implement selected CodeIt login layout

Status: READY — user approved the shared-login scope and selected prototype direction.
Owner: frontend.
Depends on: the earlier student/login polish is committed on `feat/student-ui-polish`; reconcile the intended implementation branch with the latest team base before coding.
Sources: user's selected Course-first box design; [login contract](../../specs/frontend/frontend-login.md); [shared frontend contract](../../specs/frontend/frontend-spec.md) §5.
Baseline: `feat/student-ui-polish` HEAD `88806f2` at planning time. Existing login has the original centered form with CodeIt name, administrator guidance, and pending/error feedback from the preceding polish pass. The prototype and this brief are untracked; ensure both accompany the task when using another checkout. Other untracked files exist and must be preserved.

## Subsequent user decision

The user subsequently requested the prototype’s C mark on the login panel. Use it alongside the CodeIt wordmark; this choice supersedes the earlier instruction to omit the mark and does not establish it as an official logo.

## Outcome and scope

Replace the visual arrangement of the existing `/login` screen with the selected prototype's course-first box: a compact, bordered two-part layout, with CodeIt and concise course-account copy in a pale blue panel alongside the form on wide screens; stack the panel and form on narrow screens. Preserve the team's simple CodeIt style, slate and blue colors, system typography and existing form guidance. This is the shared login for student, teacher and admin accounts; all roles must remain able to use it. Scope is the login page and focused verification; preserve shared role pages and avoid changing shared components unless necessary.

The prototype's square “C” is exploratory and is not an approved official logo. Use the existing CodeIt wordmark unless the team has an actual approved logo; do not use the Vite favicon as branding or invent an official mark. The prototype's comparison/navigation controls and sample interaction controls are not product UI.

Preserve authentication, request and response contracts, session storage, role-safe redirects, password visibility, accessible labels, username and password autocomplete, error handling, password clearing on 401, pending state, and all existing role-specific behavior. Keep prototype copy only where accurate; avoid new factual claims or promises. No backend, API, permissions, dependencies, student question workspace, teacher/admin role pages, or deployment changes are requested.

Spec delta: visual composition and any approved, accurate supporting text only. Existing login and session behavior remains governed by the linked contracts; update the login frontend spec if needed to describe the approved layout.

## Acceptance and planned verification

| ID | Observable outcome | Source | Test/manual scenario and working directory |
| --- | --- | --- | --- |
| AC-01 | Login visually follows the selected two-part box direction with established CodeIt colors and a compact form. It remains centered, readable and usable when stacked on narrow screens. | User-selected prototype | Render at narrow, intermediate and wide viewport sizes; inspect long text, zoom and overflow. Compare with the selected prototype, record viewport and deviations. |
| AC-02 | The page identifies CodeIt without claiming the prototype's C is an official logo or displaying the Vite icon as branding. Existing account guidance is accurate. | User design direction | Inspect rendered brand and copy; review assets. |
| AC-03 | Form labels, password visibility, autocomplete, keyboard focus, input and submit remain usable; pending state communicates progress and disables submission. Invalid credentials retain username, clear password and expose the existing error. | Login contract §1 | Focused behavior tests and browser keyboard/state inspection using mocks or disposable data; no live credentials required. `frontend/`. |
| AC-04 | Successful login preserves current session behavior and role-safe `next` redirects; authenticated visitors are redirected as before. Shared login remains usable for student, teacher and admin. | Login contract §§1–3; shared frontend §5 | Relevant existing or focused mocked tests for each role and permitted/denied redirects; inspect auth code diff. `frontend/`. |
| AC-05 | Error and pending states remain perceivable, text is legible, focus is visible, and no content is inaccessible on small screens. No logo or information is conveyed only by color. | Shared frontend contract; user visual request | Keyboard and accessibility-tree inspection in browser, check actual text/background contrast, and exercise error/pending at representative widths. Record actual screen-reader coverage separately. |
| AC-06 | Prior polish and unrelated work remain intact. Frontend checks and relevant tests pass or their limitations are recorded. | Repository guidance | Inspect status/diff before and after. From `frontend/`: `npm run format:check`, `npm run lint`, `npm test`, `npm run build`; record commands and outcomes. |

## Implementer handoff

Do not implement until READY. Check current branch, latest base and existing work before editing. Read the login and shared frontend specs and frontend README. Use [implement-task](../../.agents/skills/implement-task/SKILL.md) when assigned and relevant [React guidance](../../.agents/skills/vercel-react-best-practices/SKILL.md). Keep layout changes local where practical. Use meaningful behavior tests and rendered inspection; no new test stack is needed for cosmetic assertions. Record evidence, final changes and remaining limitations.

Prototype: [login exploration](../prototypes/student-login-exploration/index.html), SHA-256 `6f36be821cc940f037a44bbac36a448ec0c9e0109688ceb8b9e9fd28858cb894` at planning. Select **Course-first box · 3 of 4**. [Decision](../prototypes/student-login-exploration/decision.md) records the chosen combination. The mark is a placeholder and is not an approved logo. Preserve a stable runnable prototype for the handoff.

Unresolved: none for the approved scope. No commit, push, merge or deployment is authorized by this brief.
