# my-quizzes-local-search — Search My quizzes locally

Status: READY
Depends on: none
Sources: Approved request in this conversation; [student quiz list requirements](../../specs/product.md#student-quiz-list); [frontend snapshot and verification limits](../../frontend/README.md)
Baseline: `2f81c7e`; clean worktree at planning time.

## Outcome and scope

The current `QuizList` renders all supplied quizzes as cards, and `quizCards`
maps them in input order. Add a local search control to My quizzes. Search the
loaded quizzes by title or class using a trimmed, case-insensitive substring
query. An empty or whitespace-only query shows all loaded quizzes. Matching
results retain server order and use the existing cards, status actions, and
green classroom theme. When a nonblank query matches no quizzes, show a distinct
no-matches message and a clear-search control that restores all loaded quizzes.

This is one frontend task: update the product spec, React view and JavaScript
view-model, with executable view-model tests in the same change. Preserve the
existing card fields and status-dependent links/actions. Do not add API
requests, backend changes, sorting, or saved search preferences. No other role
or quiz behavior is in scope.

Spec delta (approved): extend `specs/product.md` under Student quiz list with
the local search contract above: trimmed case-insensitive substring matching
on title or class, blank query restores all loaded quizzes, result order stays
as supplied, and an empty result has a distinct message plus clear-search
action. This is a frontend presentation behavior; assignment visibility and
authorization requirements in P-001 and P-004 remain unchanged.

Observed implementation: `frontend/QuizList.tsx` currently renders the heading
and grid without controls. `frontend/quiz-list.mjs` creates cards from every
item in input order. Existing tests cover server order, actions, class display,
and the empty input case. The UI should filter the loaded list before card
rendering; retain the current card presentation for matches.

## Acceptance and planned verification

| ID | Observable outcome | Source | Test/manual scenario and working directory |
|---|---|---|---|
| AC-01 | A query matches a title substring without case sensitivity; surrounding query whitespace is ignored. | Approved request; spec delta | Add view-model test with mixed-case title and padded query; `frontend/` |
| AC-02 | A query matches a class substring with the same normalization; a quiz matching either title or class appears once. | Approved request; spec delta | Add tests for class-only match and title-and-class match; `frontend/` |
| AC-03 | Empty and whitespace-only queries return all loaded quizzes in their original order. | Approved request; spec delta | Add view-model boundary tests; `frontend/` |
| AC-04 | Matching quizzes retain supplied/server order, existing card data, status-dependent actions and links. | P-001; existing frontend behavior | Assert result ordering and existing `Start`, `Resume`, and `View results` behavior; `frontend/` |
| AC-05 | A nonblank query with zero matches displays a message distinct from the no-assignments state and exposes a clear-search action. Activating it restores all loaded quizzes. | Approved request; spec delta | Review React snapshot and manually exercise no-match then clear states when a host is available; `frontend/` |
| AC-06 | Search does not change the shared green classroom theme or add network/backend behavior or saved preferences. | Approved request; P-001 | Inspect the changed React view and data flow; browser visual verification requires the full application host described in `frontend/README.md`. |

Planned executable check: from `frontend/`, run `node --test
tests/quiz-list.test.mjs`. The repository snapshot does not include a browser
host, so Node view-model tests do not establish visual correctness; verify the
control, distinct empty state, clear action, cards, and theme in the full
application when available.

## Implementer handoff

First update `specs/product.md` with the approved frontend behavior, then add a
small search/filter view-model function in `frontend/quiz-list.mjs`, wire a
controlled local input and distinct no-match/clear state into
`frontend/QuizList.tsx`, and extend `frontend/tests/quiz-list.test.mjs`. Keep
filtering purely client-side and pass filtered items through existing card
mapping. No unresolved decisions or dependencies remain. Use synthetic quiz
data only; no live services, dependency installation, publication, commits, or
deployments.
