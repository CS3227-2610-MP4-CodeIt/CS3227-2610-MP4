# student-my-quizzes-local-search — Search My quizzes locally

Status: READY
Owner: Unassigned
Depends on: none
Sources: Approved user request; [product requirements](../../specs/product.md), especially P-001 and Frontend snapshot
Baseline: `e8b1790`; clean worktree at planning time

## Outcome and scope

The current React view renders every loaded quiz through `quizCards(items)` and provides no search. Add a local search control to My quizzes. It filters the already loaded quizzes by trimmed, case-insensitive substring matches against either the title or class. A blank or whitespace-only query restores all loaded quizzes. Preserve the input/server order among matches, the existing card contents and status-dependent actions, and the existing green classroom theme. When a nonblank query has no matches, show a distinct no-matches message and provide a way to clear the search.

Implement this as one frontend task, including the frontend contract update and tests. Likely affected files are `specs/product.md`, `frontend/QuizList.tsx`, `frontend/quiz-list.mjs`, and `frontend/tests/quiz-list.test.mjs`; the implementer may adjust file boundaries while keeping this scope. Do not alter backend behavior or add requests. Exclude sorting, saved search preferences, changes to card content/actions, and theme changes.

Spec delta: Extend the frontend snapshot contract in `specs/product.md` to define local title/class substring search, trimming and case-insensitivity, blank-query restoration, preserved server order, and the no-matches/clear-search behavior. The user approved this delta as part of the task.

Decisions: Match when either title or class contains the trimmed query after case normalization. Search operates only on currently loaded quizzes; no request is made as the query changes. Blank includes whitespace-only input. Preserve the relative server order of all displayed cards. Outcome, scope, exclusions, one-task breakdown, and spec change were explicitly approved in the request.

## Acceptance and planned verification

| ID | Observable outcome | Source | Test/manual scenario and working directory |
|---|---|---|---|
| AC-01 | The updated frontend contract documents search behavior and boundaries described above. | Approved user request; spec delta | Review `specs/product.md` from repository root. |
| AC-02 | A trimmed query matches a case-insensitive substring in a quiz title or class; either field independently can match. | Approved user request | Add view-model tests with mixed-case queries, leading/trailing whitespace, title-only match, and class-only match; run `node --test tests/quiz-list.test.mjs` from `frontend/`. |
| AC-03 | Empty and whitespace-only queries return all loaded quizzes in original server order. | Approved user request | Add view-model tests for blank/whitespace input and order; run the frontend view-model test command. |
| AC-04 | Matching results preserve server order and retain existing card data, status, and action URLs/text. | Approved user request; P-001 | Extend existing card tests to exercise filtered items for not-started, in-progress, and submitted states; run the frontend view-model test command. |
| AC-05 | A nonblank query with zero matches displays a distinct no-matches message and a clear-search action; clearing restores the full list. | Approved user request | Add applicable view-model coverage and inspect the React view behavior. Browser/layout verification requires the full application or an explicitly provided host; the snapshot has no browser host. |
| AC-06 | Searching uses only loaded data and causes no API request; existing theme remains in use. | Approved user request | Review implementation: filtering is client-side and no request/theme changes are introduced. |

## Implementer handoff

First update the frontend contract, then implement query filtering and the search/empty-result/clear states, with view-model tests covering matching, normalization, boundaries, order, and preserved card actions. Run `node --test tests/quiz-list.test.mjs` from `frontend/`. The repository snapshot cannot establish visual correctness without the full application or a supplied browser host; record this verification limitation if no host is available.
