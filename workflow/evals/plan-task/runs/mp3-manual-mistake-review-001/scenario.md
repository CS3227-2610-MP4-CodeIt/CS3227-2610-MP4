# Frozen simulated-user scenario

Prepared before the first worker invocation on 2026-10-20 (Asia/Singapore).
This is an assistant-simulated user, not a human usability test or a scored
harness experiment. These preferences are evaluator-private: do not place this
file inside the worker workspace. Approvals apply only to this isolated trial.

## Opening request

Use `$plan-task`. I want students to find and review their mistakes more easily
after finishing a quiz. Plan the work only; don't implement it yet.

## User preferences, fixed before observing questions

- Improve the existing submitted-results screen, not a new cross-quiz dashboard.
- Desired outcome: switch between all questions and incorrect questions only.
  Keep all questions as the default and keep the overall score visible.
- Frontend-only; use the existing own-submitted-attempt results response. No
  backend/API/schema change, new permissions, or early answer disclosure.
- Preserve the current explanations and answer labels for displayed questions.
  Do not add AI feedback, new attempts, exports, bookmarks, or a redesign.
- Perfect scores: the incorrect-only view should clearly say there are no
  mistakes and allow returning to all questions. Filter preference need not
  persist between visits or quizzes. Keep the existing question order.
- Keep existing loading/error/retry behavior and keyboard accessibility.
- Prefer one small coding task with its spec delta and tests. Accept more only
  if the worker identifies genuinely separate user outcomes; reject unnecessary
  splitting of code, spec and tests into dependency-heavy tasks.
- Approve this bounded scope if accurately proposed. Ask for a correction if
  a proposal contradicts these preferences. If asked for unspecified low-risk
  presentation detail, accept the existing project convention/recommendation.
- No teammate is assigned this specific mistake-filter task in the scenario;
  existing quiz-discovery work is separate, but shared-file coordination remains
  relevant if discovered.

## Interaction policy and stopping rule

Read each actual worker response before answering. Answer its questions using
the preferences above, without quoting the skill or private assessment criteria.
Do not send pre-scripted follow-ups regardless of what the worker asks. Do not
rescue an unapproved READY result by retroactively treating it as approved.
Stop at a completed brief, an explicit blocker, an unsafe/out-of-scope action,
or six worker turns. Each worker invocation has a 600-second timeout.

## Assessment, without a fabricated percentage

Mechanically inspect changed paths, per-turn artifact timing, successful skill
reads, protected-input hashes, required brief sections and local references.
Review semantically whether questions address real unresolved decisions,
settled choices carry forward, the final scope is approved and small, and each
acceptance criterion has a meaningful planned verification. Metadata defects
are reported separately from whether elicitation and scope planning worked.
The same assistant answers and reviews: this is exploratory evidence, not an
independent semantic jury or a reliability estimate.
