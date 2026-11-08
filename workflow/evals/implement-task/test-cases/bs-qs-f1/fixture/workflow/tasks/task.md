# Local search in My quizzes

**Status: READY**

## Outcome

Students can narrow the quizzes already loaded in **My quizzes** with a local
search. Searching matches a trimmed, case-insensitive substring of either the
quiz title or class name. A blank or whitespace-only query shows every loaded
quiz again. The filtered list retains server order and the existing cards,
status-dependent actions, and green classroom theme.

When a nonblank query matches no quizzes, show a distinct no-matches message
and provide a clear-search action that restores the full loaded list.

## Approved scope

- Add controlled search input and clear-search affordance to the existing
  `QuizList` view.
- Add filtering to the frontend view model in `frontend/quiz-list.mjs`; match
  against `title` and `class_name` after trimming the query, ignoring case.
- Render cards from the filtered items while preserving their input order and
  existing card fields, links, and status-dependent actions.
- Update `specs/product.md` with the approved student-facing behavior.
- Add view-model tests in `frontend/tests/quiz-list.test.mjs` for matching,
  blank-query restoration, ordering, and unaffected card actions. Cover the
  no-match state and the clear-search control in the view change or available
  snapshot-level checks.

## Exclusions

- No API requests or backend changes.
- No sorting, persistence, or saved search preferences.
- No changes to quiz eligibility, card content, action destinations, or theme.
- No implementation outside this single task.

## Product spec delta

Add a student quiz-list requirement to `specs/product.md`: My quizzes supports
local title-or-class substring search using a trimmed, case-insensitive query;
blank input restores all loaded quizzes; filtering preserves server order; and
no matches have a distinct message and clear-search action. This makes explicit
the approved behavior for P-001's quiz list without changing assignment or
attempt rules.

## Implementation notes

The current `QuizList` receives `items` and renders `quizCards(items)` directly.
Keep filtering on those supplied items, before card rendering; do not fetch on
query changes. Keep the original items intact so clearing the query restores
them. Reuse the existing card mapping to preserve card structure and actions.
The current frontend snapshot has no React/browser test host, so keep the
matching logic testable in the JavaScript view model and make the view-level
no-match and clear affordance visible in the snapshot.

## Acceptance criteria

1. A query with leading/trailing whitespace is trimmed before matching; a
   whitespace-only query returns all loaded quizzes.
2. Matching is case-insensitive and checks substrings in either title or class
   name. A quiz matching both fields appears once.
3. Search filters only the supplied loaded items, preserves their relative
   server order, and does not alter card fields, status-dependent actions, or
   links.
4. A nonblank query with zero matches displays a message distinct from the
   ordinary empty list and exposes a control that clears the query. Clearing
   restores all supplied quizzes.
5. Search introduces no API activity, backend behavior, sorting, or persisted
   preferences, and the existing theme remains intact.
6. `specs/product.md` documents the behavior above, and the frontend tests cover
   the view-model behavior and regression of existing actions.

## Verification

- From `frontend/`, run `node --test tests/quiz-list.test.mjs`.
- Review `QuizList.tsx` and `student.css` to confirm the search, distinct
  no-match state, clear action, and theme/card presentation.
- The repository snapshot has no browser host; the Node tests do not establish
  visual correctness. Browser verification requires the full application or an
  explicitly provided host.

## Dependencies and blockers

None. The approved behavior is consistent with the current frontend data flow;
no blocking conflict was found.
