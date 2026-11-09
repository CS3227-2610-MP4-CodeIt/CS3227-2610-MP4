# Student workbench guidance, draft status, and mobile shortcuts

Status: READY — user approved the scope and task breakdown on 2026-11-09.
Depends on: none
Sources: User request and prototype at `/Users/junhaong/Documents/y3s1/CS3227/CS3227-Planning/CS3227-MP4-Planning/prototypes/student-workbench-five-fixes/index.html`; `specs/frontend/frontend-student.md` §§1, 3.
Baseline: `af4e3c2`; unrelated worktree changes exist.

## Outcome and scope

Improve the student question workspace with (1) question-mark help for input/output and the three actions, (2) visible local-draft save status, and (3) in-page shortcuts to Problem, Editor, and Results on narrow screens. The current workspace already provides draft persistence, Run / Submit / Get hint, result tabs, and a stacked narrow-screen layout, but has no save indicator, action help, or section shortcuts.

Implement the three UI changes in the existing student question workspace and update `specs/frontend/frontend-student.md` to describe the agreed behavior. No backend or data contract change is expected. Keep Run, Submit, Get hint, result tabs, existing localStorage key/behavior, and stacked layout intact.

Out of scope: editor-versus-result code comparison, screen-reader live announcements, assignment question-number/arrows navigation, new persistence guarantees, and changes to backend behavior. The prototype's illustrative questions and simulated actions are not product requirements.

## Decisions

- **Action help:** Use a question-mark help control with hover and keyboard-focus disclosure. Include this copy:
  - **Input and output:** “Read input from standard input using `input()`, and write output using `print()`. Follow the format in the problem statement.”
  - **Run:** “Checks visible tests.”
  - **Submit:** “Checks all tests and records your submission.”
  - **Get hint:** “Offers an instructional nudge.”
- **Draft status:** Show “Saving draft…”, “Draft saved on this device”, and “Draft could not be saved on this device.” Reflect the existing debounce and localStorage failure handling; status must not imply a server save.
- **Narrow-screen shortcuts:** Show Problem / Editor / Results in-page links to the existing sections at narrow widths. This explicitly does not include question number/arrows, which navigate assignment questions and were excluded from scope.
- **Prototype:** Use only the above elements from the referenced prototype; it is outside the implementation repository, so the implementer may need access to the planning checkout.

## Acceptance and planned verification

| ID | Observable outcome | Source | Test/manual scenario and working directory |
|---|---|---|---|
| AC-01 | Question-mark help exposes the specified input/output and action descriptions on hover and keyboard focus, and can be operated without obscuring or trapping the workspace. | User decision; prototype; frontend-student §3 | Frontend component tests for content and keyboard access; manual desktop pointer and keyboard check (`frontend/`). |
| AC-02 | After an editor change, status reflects pending save, successful local save, and unavailable/failed local storage; once saved it says the draft is on this device. Existing editing remains usable when storage fails. | User decision; frontend-student §1.1 | Tests with controlled timers and localStorage success/throwing behavior, including transition back to saved (`frontend/`). |
| AC-03 | At narrow viewport widths, Problem / Editor / Results shortcuts navigate to the corresponding existing sections; at wide widths they are not shown. The page remains stacked and usable. | User decision; frontend-student §3 | Responsive component/browser check at widths on both sides of the chosen breakpoint (`frontend/`). |
| AC-04 | Existing draft keying, debounce, page-exit flush, job actions, result tabs, and submission workflow continue to work. | frontend-student §§1–3 | Existing focused student frontend tests plus relevant regression coverage (`frontend/`). |
| AC-05 | Student frontend spec records the visible save states, help content/interaction, responsive shortcuts and their behavior. | Repository guidance | Review the updated spec against implementation and acceptance criteria. |

## Implementer handoff

First inspect `frontend/src/features/student/QuestionPage.tsx`, `useDraftSaver.ts`, `drafts.ts`, and frontend component conventions, then implement the three scoped behaviors and tests. Use `.agents/skills/implement-task/SKILL.md`; because this changes React UI, also apply `.agents/skills/vercel-react-best-practices/SKILL.md`. User approved this scope and task breakdown on 2026-11-09. Implementation is a separate next step.
