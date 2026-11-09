# Student code complexity analysis

**Status: READY — scope approved by user.**

## Outcome

In the student question workspace, a student can request a complexity analysis of their own submitted Python code and see a clear Big O time and auxiliary-space summary, plus a plain-language explanation of how loops, recursion, and data structures affect those estimates. Best-effort estimates must state assumptions and uncertainty rather than imply certainty.

## Proposed scope

- Add a `complexity` student job using the existing authenticated backend job and SoCLaaS integration pattern.
- Analyze only a code snapshot belonging to the student's completed submission, never the current unsubmitted editor draft. A submission review action captures the existing submission ID/code and ties the result to that immutable snapshot.
- Return structured time and auxiliary-space complexity labels, an explanation, and explicit assumptions/caveats. Do not use hidden tests, execute student code, produce grading outcomes, or modify submissions.
- Add a workspace action and result panel/tab with in-progress, success, failure, and empty states. Explain that output is an estimate.
- Update the student frontend and backend specifications and add focused frontend/backend tests.

## Out of scope

- Deterministic/static analyzer, compiler-grade proof, execution profiling, support for languages other than Python, complexity grading, teacher/admin views, persistent analysis history, or changes to code execution and submission behavior.
- Guaranteeing asymptotic estimates for arbitrary dynamic Python; uncertain cases remain best effort with explicit assumptions.

## Proposed interaction

Keep the existing workspace actions and Run result, Submit result, Hint, and Submissions tabs intact. In Submissions, the student selects a row to show its existing read-only code and Load into editor action. Add a Complexity analysis section below that code, with an Analyze action and its result, following option 3 in the [prototype](../prototypes/complexity-analysis/index.html). The action is scoped to the selected submission's stored code; editing the current draft or loading another submission cannot alter the analysis input. Analysis is available for the student's own submitted code after the submission has completed, including submissions with non-accepted verdicts, to support post-attempt learning.

## Proposed service contract

- Student-only `POST` and `GET` endpoints under `/student/assignments/{aid}/questions/{qid}/submissions/{sid}/complexity`, validating current membership, question-in-assignment, submission ownership, and completed submission state.
- New job kind `complexity`, keyed by `a{aid}:q{qid}:s{sid}` per student so different submissions are analyzed independently.
- Structured success result: time complexity, auxiliary-space complexity, explanation, and assumptions/caveats. Response validation and output-size bounds are required; model output is not authority and must not trigger tools or code execution.
- Send only the admitted student's submitted code and the minimum necessary question title/context, if any, to the model. Never include hidden tests, reference solutions, other students' data, or credentials. Prefer code-only analysis if question context is not needed.
- Apply the existing injection scan, untrusted-data wrapping, per-job canary/output validation and bounded LLM timeout. Do not enable tools for this analysis.

## Security and privacy planning

Assets: student code, account/membership data, hidden tests/reference solutions, AI credentials, and job state. Actors: authenticated student, other students, model gateway, and browser.

Threats and planned controls:

1. Unauthorized access or cross-student disclosure: require student role and `_get_assignment` membership/question admission; use owner-scoped generic job reads. Test allowed member and denied non-member/wrong-role requests, including no job creation on denial.
2. Prompt injection in comments/docstrings or forged instructions in model output: scan inputs; wrap code as untrusted; system prompt states code is data; no model tools; enforce output schema/length and canary. Test adversarial code alongside benign code that still receives useful analysis; malformed, oversized, canary-bearing output fails closed.
3. Hidden-test/reference-solution leakage: do not fetch or send test cases/solutions; verify model request payload excludes them and results contain no server-only context.
4. Resource exhaustion / duplicate work: preserve 64 KiB input cap, bounded output/tokens and configured job timeout; verify duplicate in-progress request reuses job and concurrent requests do not multiply model work.
5. Overstated estimates: require explicit assumptions and caveats for dynamic dispatch, input-dependent recursion, or otherwise ambiguous constructs; label space as auxiliary space and distinguish it from total process memory.

Affected matrix references: AUTH-04, DATA-01, JOB-01, AI-01, AI-02. Add a dedicated row when implementation establishes the exact flow; planned tests must be recorded as planned until run.

## Acceptance criteria

1. No complexity analysis is available from unsubmitted editor contents. Analysis can be requested only from a completed submission review and uses that submission's stored code, whether its verdict is accepted or not.
2. A successful result clearly displays Big O time and auxiliary space plus a readable explanation connecting identified loops, recursion, and data structures to estimates, with assumptions/caveats where needed.
3. The existing submission table, selected code, Load into editor action, and workspace tabs remain available. The selected submission's complexity section identifies its context and has understandable loading, failed, and retryable states; another job type’s status/result is not shown as complexity output.
4. Only the submission owner with current assignment membership can start/check analysis; another user cannot read the result, and pending/inaccessible/wrong-question submissions are denied.
5. Code stays within existing request limits, remains unexecuted, hidden tests/reference solutions are excluded, and the model has no tools.
6. Prompt-injection, malformed model response, output bound, denied access, job deduplication, and benign useful-analysis cases have focused tests.
7. Relevant frontend/backend specs document the route, job kind, result schema, UI behavior, model-data boundary, estimates/caveats, and limitations.

## Verification path

- Backend: targeted student endpoint/job tests and relevant AI guard/output validation tests; Ruff, mypy and backend test suite as practical per `backend/README.md`.
- Frontend: focused question workspace tests; format, lint, tests and build per `frontend/README.md`.
- Security acceptance: inspect model payload construction and run adversarial/benign mocked-model tests; update the affected security-matrix rows with observed evidence only.
- No live SoCLaaS call is required for automated tests. Manual browser verification should confirm current-buffer snapshot behavior and readable responsive presentation.

## Decisions captured

- User requested a student-side feature in the question workspace showing time and space Big O and plain-language explanation of loops, recursion and data structures. User clarified that analysis should be post-submission for student review and learning, to avoid giving assignment guidance on an unsubmitted draft.
- User explicitly requested subagents for the implementation workflow.
- User selected AI explanation using the existing AI job path rather than a static-analyzer-only feature.
- User selected best-effort estimates with explicit assumptions for uncertain cases.
- User selected prototype option 3: a complexity analysis section below the selected submission's code, preserving the existing workspace and its features.

## Approval needed

Single-task scope, proposed job/API shape and exclusions approved by user.
