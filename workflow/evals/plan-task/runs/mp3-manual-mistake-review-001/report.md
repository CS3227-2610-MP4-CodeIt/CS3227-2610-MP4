# Plan-task: adaptive clarification smoke trial

Date: 2026-10-20 (Asia/Singapore). Method: assistant-simulated user,
manual `codex exec` / `codex exec resume`, one conversation.

**Result: useful task output and a successful clarification checkpoint, but the
separate final scope-confirmation step was skipped.** The worker inspected the
real application, asked a relevant product question, waited for an answer, and
then produced one frontend task. It did not implement anything. This is an
exploratory review, not a scored harness experiment or an independent jury.

## Runtime and provenance

| Worker turn | Action | Process wall time | Exit code |
|---|---|---:|---:|
| 1 | Inspect current behavior; ask which review mode is wanted | 63.714 s | 0 |
| 2 | Resume with the actual answer; write and inspect the brief | 77.586 s | 0 |
| Total | Two calls in the same session | **141.300 s** | Both successful |

Times measure each CLI process, including its startup/shutdown and tool work.
They exclude evaluator preparation, time composing the reply, permission
approval, and report writing; they are not total elapsed session time. Mean
worker-turn time is 70.650 s, but the two turns do different work and are not
repeated trials.

- CLI: `codex-cli 0.161.0`.
- Recorded worker: `gpt-5.6-luna`, low reasoning effort; no model/effort override.
- Session: `01a1577c-29a3-7e62-9021-c9fd861a4166`.
- Source repository revision: `ee7e3b9dd31b6bea95c6cdd15d8875d90ad3880b`.
- Prepared disposable revision: `3a91516753592fa9e5f2b1ffff7a375d62de8d50`.
- Live JSONL usage summed across both turns: 486,571 input tokens, including
  368,896 cached input tokens; 5,162 output and 640 reasoning-output tokens.
  These are the CLI's reported fields, not a monetary-cost estimate.

See [setup and initial file hashes](setup.json),
[measured observations](observations.json), and the
[captured session rollout](worker-rollout.jsonl).

## Setup and isolation

The input was the actual tracked repository snapshot, not the small synthetic
empty-state fixture used in experiment-001. The current untracked `plan-task`
skill and existing quiz-discovery brief were copied in before a clean local
baseline commit. Dependencies, ignored local data and the original `.git/`
were not copied. Other tracked project skills, profiles and historical workflow
files remained available. This was not a skill-isolated baseline comparison.

The [private scenario](scenario.md) fixed the simulated user's preferences
before the first invocation. It and this manual trial's evaluator files were
outside the worker workspace. The archive still included the repository's
already-tracked eval framework/history; “no evaluator files” in the setup
policy means this trial's private files and the untracked plan-task suite,
not removal of every tracked evaluation-related file.

The starting request was deliberately underspecified about the review design.
The frozen user wanted the existing results page, an optional mistakes-only
filter, all questions as default, frontend-only work, no new AI/data/permission
boundary, and one small implementation task. Only answers relevant to actual
questions were sent. Hidden preferences were not pasted into the worker prompt.

The first launch failed before a worker session began because the outer app
sandbox could not initialize Codex session storage. Its
[diagnostics](launch-attempts/sandbox-startup-failure/stderr.log) were retained.
The same opening prompt was retried with permission to run the CLI; the worker
itself still requested `workspace-write` sandboxing. The failed launch took
0.449 s and is excluded from the successful worker total above.

The successful calls also logged environment warnings, including unrecognized
managed settings and a model-catalog refresh timeout. Both completed with exit
code 0. Global Codex configuration and installed skills were not isolated.

## Actual conversation

1. **Opening request:**
   > Use `$plan-task`. I want students to find and review their mistakes more easily after finishing a quiz. Plan the work only; don't implement it yet.

   The worker identified that scores, selected answers, correct answers and
   explanations already exist. It offered three designs: incorrect-only plus
   all questions, an emphasized all-question view, or incorrect-only by default.
   It recommended the first and stopped to ask. No files changed in this turn.
   [Exact prompt](turns/turn-01/prompt.md) ·
   [full response](turns/turn-01/response.md) ·
   [trace](turns/turn-01/trace.jsonl) ·
   [immediate state](turns/turn-01/state.json).

2. **Reply chosen after reading that question:**
   > 1. Keep all questions as the default, with an option to show only incorrect ones.

   The same session retained the choice and produced
   `workflow/tasks/student-results-mistake-review.md`, marked `READY`.
   It defined one frontend slice and eight acceptance criteria, including mixed
   results, no mistakes, one/all mistakes, keyboard operation and existing
   submission/answer-disclosure guards.
   [Exact reply](turns/turn-02/prompt.md) ·
   [full response](turns/turn-02/response.md) ·
   [trace](turns/turn-02/trace.jsonl) ·
   [immediate state](turns/turn-02/state.json).

There was no scripted unconditional follow-up, third worker turn, silent repair,
or retry of the worker's planning behavior. The trial stopped at the completed
brief, as specified before launch.

## Checks and findings

| Check | Observed result |
|---|---|
| Reads the target skill and brief format | Successful command output contains both complete files. |
| Grounds planning in current application behavior | Inspects existing tasks, frontend/backend specs, `QuizPage.tsx`, API types and student test definitions; correctly identifies a missing filtering convenience rather than missing results support. |
| Asks before choosing an unresolved user-visible behavior | Yes; gives options, a recommendation and trade-offs, then waits without writing a brief. |
| Carries the answer into the plan | Yes; default all questions and optional incorrect-only are retained in the outcome and acceptance criteria. |
| Confirms the final bounded task before READY | **Gap.** The only explicit approval is of review mode/default. It does not present frontend-only scope, exclusions and one-task granularity for confirmation before marking READY. AC-08 nevertheless calls the expanded scope “Approved scope”. |
| Keeps tasks small and coherent | One user outcome with its code/spec/tests; no artificial layer-level task split. |
| Follows the brief format | Has status, dependencies, sources, a real baseline revision, all three required sections and eight acceptance rows with planned checks/working directories. |
| Provides useful verification rather than keyword-only promises | Each criterion has a relevant component test or browser/diff check. Commands match the existing frontend scripts; checks remain clearly labelled planned. |
| Handles security proportionately | Uses existing own-submitted results and server `is_correct`; preserves early-disclosure/ownership guards. No changed data or permission boundary requires a new threat model for this scope. |
| Preserves unrelated files and protected inputs | Hash comparison finds only one added brief. No product, spec, Developer Guide, existing task, skill or profile changes. The frozen scenario hash also remains unchanged. |
| Local references and whitespace | All eight local links resolve to files, and the two referenced spec headings exist in the disposable workspace. The new brief passes `git diff --no-index --check /dev/null <brief>`. |

The key distinction is that its **content is mostly suitable**, but its claim
of full approval is stronger than the recorded conversation. Selecting a mode
could reasonably authorize that behavior; it does not separately demonstrate
the skill's instruction to confirm the complete task scope, exclusions and
granularity. Under that literal completion rule, the READY handoff is premature.
No corrective prompt was sent to conceal this result.

The [verbatim output copy](artifacts/workflow/tasks/student-results-mistake-review.md)
is preserved with [Git status](git/status.txt) and the
[complete added-file patch](git/untracked.patch). Its internal links are
repository-relative and were validated in the original disposable layout;
the standalone artifact copy does not contain the referenced source tree.
The original, fully linked brief remains at
`/tmp/quizit-plan-task-manual.1vv63y/workspace/workflow/tasks/student-results-mistake-review.md`.

## What this establishes—and does not

This run demonstrates a real ask → answer → resumed planning path without
guessing a fixed question order in advance. It is suitable exploratory evidence
for adaptive interaction and exposes a concrete approval-boundary gap.

It does not establish reliability, implicit activation, revision handling,
complex task splitting, security-sensitive planning, or correct behavior over
several clarification rounds. There was one explicit skill invocation and one
clarification round. The same assistant simulated the user and reviewed the
result; no independent semantic jury or numeric grade was run.

The output happened to match the other frozen preferences, but the worker did
not elicit them. Matching an undisclosed preference is not evidence that it
asked about or obtained approval for it. Approvals in this simulated
conversation do not authorize implementing the feature in the main repository.

No application tests, live app/browser checks or live AI product calls were
run. Test plans were inspected, not executed. The target skill, existing suite,
existing reports, harness code and Developer Guide were not changed by this
trial. Nothing was committed or pushed.
