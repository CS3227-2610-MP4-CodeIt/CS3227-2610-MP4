# student-login-ui-polish — clear, accessible student pages and login

Status: READY — approved scope; no unresolved product decisions.
Depends on: none.
Sources: user's approved student/login polish request and instruction to implement on `feat/student-ui-polish`; [shared frontend contract](../../specs/frontend/frontend-spec.md), [student contract](../../specs/frontend/frontend-student.md), [login contract](../../specs/frontend/frontend-login.md).
Baseline: `455a4d2163088047b9db87f3d5c35378b58ea707`, branch `feat/student-ui-polish`. No tracked changes at task revision. An interrupted attempt left untracked `frontend/src/components/CopyButton.test.tsx` and `frontend/src/features/student/ResultTabs.test.tsx`; these are unfinished task work, not passing evidence or an approved component design. Unrelated untracked evaluation artifacts must remain untouched.

## Outcome and scope

Students should be able to navigate their assignments, understand editor and hint context, perceive state changes, and recover from small failures through a consistent, simple interface. The shared login should clearly identify CodeIt and communicate waiting and errors.

Current gaps established from source and limited browser checks:

- Meaningful secondary metadata uses faint text colors; the existing slate-400/white token pairing calculates below the normal-text contrast threshold. Actual rendered backgrounds still require verification.
- Async error, draft and job text lacks intentional announcements. Result controls expose tab roles without complete keyboard and panel relationships. Tab/Enter still works, including opening submission history; the workflow is not wholly mouse-only.
- Narrow-screen Problem/Editor/Results shortcuts exist only at the top of a long page. Some compact controls are difficult touch targets.
- The hint question relies on a placeholder for its visible explanation; Python and initial editor-content provenance are not consistently identified.
- Pending login disables an unchanged button label; Copy handles success without an actionable rejection/unavailability path.
- Student/list/detail/login typography and spacing can be made more deliberate while retaining the established visual language.

Primary scope: the three student routes (`/student`, `/student/assignments/:aid`, `/student/assignments/:aid/questions/:qid`) and `/login`. Work in `frontend/src/features/student/`, `frontend/src/features/login/LoginPage.tsx`, relevant focused tests, and affected frontend specs.

Permitted shared overlap: narrow changes to Layout, Spinner, ErrorText, JobStatusBadge, CopyButton, `frontend/src/index.css`, and the browser title in `frontend/index.html`. Check effects on teacher/admin screens when those primitives change; leave their page-specific components and workflows unchanged.

Decisions and exclusions:

- The user owns student work and explicitly requested this bounded implementation. Preserve neutral surfaces, a blue accent, compact top navigation, system typography, tables/forms/panels, the two-column desktop coding workspace, and narrow stacking. No sidebar, three-pane redesign, replacement component library, theme system or decorative expansion.
- Keep styling in the existing Tailwind/component conventions and `index.css`; do not add a separate stylesheet contrary to the frontend contract.
- Preserve class grouping/question order, solved/deadline semantics, safe Markdown, hidden-test privacy, existing APIs/auth, independent jobs, local drafts, result timestamps, history, overwrite confirmation, and submission-bound complexity analysis. Zero solved questions does not establish that an assignment is unattempted.
- Do not change backend code, LLM inputs/outputs, permissions, dependencies, workflow tooling or deployment. No new live AI/execution calls are required for this UI task.
- Implementation choices within these boundaries belong to the implementer. Existing partial tests may be corrected; they do not prescribe helper names or component extraction.

Spec delta: approved within this task are visible editor/hint context, truthful code-origin feedback, complete result-tab interactions, narrow section access while working, explicit login progress/error feedback, clipboard failure recovery, reduced-motion loading, and restrained visual consistency. Update the affected frontend specifications alongside those changes. Auth/session, request payloads, draft precedence/persistence, job behavior, grading and access rules remain unchanged.

## Acceptance and planned verification

| ID | Observable outcome | Source | Test/manual scenario and working directory |
| --- | --- | --- | --- |
| AC-01 | Meaningful secondary text is readable on its actual background, meeting 4.5:1 for normal text where applicable. Existing neutral/blue identity is retained. | Approved accessibility scope | Inspect actual token/background pairings and rendered states; exclude genuinely disabled/decorative text from inappropriate contrast claims. Frontend source and browser. |
| AC-02 | Login errors and meaningful draft/job/reconnect/copy changes have deliberate programmatic feedback. Elapsed seconds and entire code/result bodies are not repeatedly announced. Existing error/retry handling remains usable. | Approved feedback scope; shared frontend contract | Focused behavior/semantics checks and keyboard/accessibility inspection. Distinguish source/live-region verification from actual screen-reader speech testing. |
| AC-03 | Results have a named tablist, stable linked tabs/panels, selected state and one tab stop. Arrow keys wrap, Home/End work, Tab leaves normally, and action buttons still select the matching result view. History remains keyboard accessible. | Approved tabs delta; student §3 | Test navigation/selection relationships, then exercise keyboard behavior in a rendered workspace. `frontend/` and browser. |
| AC-04 | On narrow screens, students can return between Problem, Editor and Results while working without returning to the top of the long statement. Section destinations are reachable/focusable and not covered by navigation. Desktop split remains intact. | Approved navigation delta; student §3 | Long statement/title at narrow, intermediate and laptop widths. Check anchors, focus and layout; record actual viewport and tooling limits. Browser. |
| AC-05 | The optional hint question has a persistent visible label/explanation and the editor identifies Python. Initial/restored code origin is communicated truthfully and does not imply that edits are submitted or server-saved. | Approved orientation delta; student §1 and §3.2 | Exercise local draft, latest submission, empty initialization, subsequent edits and confirmed history loading as applicable. Preserve initialization precedence and existing local-draft behavior. Focused tests plus browser. |
| AC-06 | Login identifies CodeIt, gives accurate account guidance, and communicates pending state. Invalid login retains username, clears password and exposes an understandable error. Existing role-safe redirects and session handling remain intact. | Approved login delta; login §1–3 | Mock pending/success/failure where appropriate; inspect form, labels, error and busy states in browser. No new signup/reset capability. `frontend/`. |
| AC-07 | Copy success remains clear; rejected or unavailable clipboard access produces perceivable failure feedback and a manual-selection fallback. Failure does not imply copying succeeded. | Approved recovery delta | Focused success/rejection/unavailability behavior tests and rendered feedback check. Clipboard failures may be mocked; label evidence honestly. `frontend/`. |
| AC-08 | Shared navigation contains long account text and keeps links/logout reachable at narrow widths without page-level horizontal overflow. Touch hit areas improve where needed, desktop density remains useful, and loading meaning survives reduced motion. | Approved shared scope; shared frontend contract | Student/teacher/admin shell at representative narrow/intermediate/laptop widths and long text; reduced-motion check. A 44px comfort recommendation is not a blanket WCAG AA rule. Browser/static checks. |
| AC-09 | Headings, labels, sections, spacing and metadata are consistent across student list/detail/workspace and login. Existing data, grouping, ordering and solved counts remain accurate; empty states give truthful guidance. | Approved visual goal; student §2 | Render empty/populated lists and long content; compare representative screens. No unit tests that merely mirror cosmetic classes. Browser/static review. |
| AC-10 | Drafts remain device-local and persist through navigation/submit/logout; history stays read-only until confirmed restoration; results retain sent-time context; hidden-test data stays private; complexity targets the selected stored submission. | Student §1–3; shared frontend contract | Existing relevant regressions and focused tests for affected behavior. Use synthetic/mocked boundaries where needed; distinguish UI checks from live judge/provider checks. `frontend/`. |
| AC-11 | Final frontend format, lint, test and build checks pass; final diff remains in scope. Shared effects and acceptance coverage are recorded with explicit gaps rather than assumed passes. | Repository verification guidance | From `frontend/`: `npm run format:check`, `npm run lint`, `npm test`, `npm run build`, using available dependencies. Inspect final diff and browser evidence after last changes. |

## Implementer handoff

First verify branch, HEAD and pre-existing changes, then inspect current source/specs and the two incomplete test files. Reconcile already-satisfied criteria instead of inventing replacement work. No prototype is required: preserve the current composition and settle minor layout choices within the approved scope.

Follow [implementation guidance](../../.agents/skills/implement-task/SKILL.md), [project standards](../../.agents/skills/code-review/references/project-standards.md), and relevant [React guidance](../../.agents/skills/vercel-react-best-practices/SKILL.md). Use existing tooling from [frontend README](../../frontend/README.md). Test changed behavior meaningfully; use visual/manual checks for presentation. Do not install a new testing stack for cosmetic assertions.

Verify the edited-source frontend rather than assuming an existing local container reflects the working tree. A separate loopback Vite instance is acceptable; leave existing services and production untouched. Record any started service and its stop method. Preserve existing coursework and drafts during browser checks; use disposable/mock cases for failure states.

The caller assigns supporting evidence/review output destinations. Record exact final changed paths, checks actually run, evidence level, remaining gaps and final target fingerprint for review. Resolve material scope/contract conflicts before dependent edits. No commits, pushes, merges or deployment are authorized by this task.
