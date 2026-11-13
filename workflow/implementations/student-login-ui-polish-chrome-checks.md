# Student login UI — Chrome contrast follow-up

Status: **IMPLEMENTED** for the assigned verification follow-up, pending specification and verification re-review. Task: [brief](../tasks/student-login-ui-polish.md); assigned contrast disagreement: [correction-2 review](../reviews/student-login-ui-polish-correction2.md). HEAD `455a4d2163088047b9db87f3d5c35378b58ea707`, branch `feat/student-ui-polish`; starting/final tracked diff SHA-256 `2909b5f40c14837cc09ba429d873f456c8b474b618e67686645800a201d7807a`. The seven untracked source/test hashes match [correction-2 handoff](student-login-ui-polish-resume-correction-2.md). No source, test or specification files changed in this follow-up; this evidence file is the only new path. Existing task work and unrelated artifacts were preserved. No commits.

## Method and outcome

The implementer inspected affected Tailwind/component source for opacity, translucent text/background classes and hover/focus styling. The only application opacity utility in those areas is `disabled:opacity-50` on shared buttons; CodeMirror supplies a translucent active-line background and an animated cursor layer. The user authorized Chrome and Playwright. An isolated headless context of the installed Chrome was launched by a disposable Playwright script (`/tmp/codeit-contrast-chrome.cjs`) against edited-source Vite at `127.0.0.1:5192`; all API data were intercepted and synthetic, no existing Chrome profile or real coursework was accessed. `frontend/`: `node /tmp/codeit-contrast-chrome.cjs > /tmp/codeit-contrast-chrome-results.txt` exited 0. The Vite process was stopped with Ctrl-C; no Docker or live AI/judge was necessary. The temporary script/output are ephemeral and not durable regression tests.

The script measured actual Chrome computed foreground/background styles for each control in normal, pointer-hover and separately focused states, converting each CSS color via canvas to 8-bit sRGB; it composited transparent background layers over their ancestors, applied element opacity, then calculated relative-luminance contrast. It asserted 4.5:1 for the sampled enabled controls. Results (normal / hover / focus):

| Enabled control | Ratios |
| --- | --- |
| Assignment link | 6.83 / 6.83 / 6.83 |
| Log out, Run, Get hint, Copy | 10.36 / 9.90 / 10.36 |
| Submit and Log in | 5.25 / 6.83 / 5.25 |
| Unselected Hint result tab | 7.58 / 6.92 / 7.58 |

In an actual rendered editor with synthetic `# comment`, a string and `print(42)`, the active line's `rgba(204,238,255,0.267)` was composited over white: sampled active-line dark text was **16.86:1**, green number text **6.60:1**; sampled comment and string text on white were **6.60:1** and **7.51:1**. The animated cursor layer had no text. A rendered-elements inventory found no other partial-opacity/translucent backgrounds in that sample. On the separate login screen the disabled button's 0.5 group opacity composited to approximately **2.20:1**; this genuinely disabled control is excluded from the normal-text contrast requirement, as the task specifies. No enabled sampled text failed.

Keyboard Tab navigation gave the enabled login button Chrome's `rgb(0,95,204) auto 1px` focus outline. Programmatic focus of the hint input exposed its blue focus border and no outline; source uses a border focus treatment. The test measured text contrast and observed focus styling; it did not assert conformance of every non-text focus indicator. It did not test every possible code syntax color, live state, user agent or real-device rendering. This does not convert representative sampling into exhaustive coverage; reviewers should reconcile the stated acceptance disagreement using this evidence and prior [correction-2 rendered-state results](student-login-ui-polish-resume-correction-2.md). Actual screen-reader speech and live services remain untested.

## Checks

Implementer, `frontend/`: `npm run format:check`, `npm run lint`, `npm test`, `npm run build` all exited 0; **18 files / 65 tests** passed. Lint emitted six Fast Refresh warnings and Vite emitted the chunk-size warning. Root `git diff --check` exited 0. No product defect was observed and no application changes were made, so no red test was manufactured. No new review finding ID was assigned to the contrast disagreement; this addresses its requested AC-01 investigation. Prior `CQ-student-login-01`, `SC-student-login-01`, and `VR-student-login-01` remain subject to independent review's earlier dispositions.
