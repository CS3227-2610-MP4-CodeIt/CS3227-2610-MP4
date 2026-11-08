# Add local search to My quizzes

**Status:** READY

## Outcome

Students can narrow the already loaded quizzes on **My quizzes** with a local
search. A trimmed, case-insensitive query matches a substring in either the
quiz title or class name. A blank query shows all loaded quizzes. The list
keeps server order, existing cards, status-dependent actions, and the shared
green classroom theme.

When a nonblank query matches no quiz, show a distinct no-matches message and
provide a clear-search control that restores the full loaded list.

## Scope

- Add search state and filtering to the student quiz list frontend.
- Add the search input and clear-search interaction to the My quizzes view.
- Update `specs/product.md` to make this approved student quiz-list behavior
  part of the product contract.
- Extend frontend view-model tests for matching, trimming, case handling,
  matching either field, blank-query restoration, and preservation of input
  order and card actions. Cover the no-matches and clear-search view behavior
  in the available frontend test approach where practical.

## Exclusions

- No new API requests, backend changes, sorting, or saved search preferences.
- No changes to quiz card content, status actions, or theme.
- No search across fields other than title and class.

## Acceptance criteria

1. The search input filters the loaded quizzes by substring of title or class;
   matching ignores letter case and leading/trailing whitespace in the query.
2. A blank or whitespace-only query restores every loaded quiz.
3. Filtering preserves the relative server order of matching quizzes.
4. Existing card content and status-dependent actions remain intact for
   filtered results.
5. A nonblank query with zero results displays a distinct no-matches message
   and a usable clear-search control; activating it clears the query and shows
   all loaded quizzes.
6. The existing shared green classroom theme remains in use.
7. Product spec and frontend tests describe and verify this behavior. No
   backend or API work is introduced.

## Spec delta

Add the local search behavior to the **Student quiz list** requirements in
`specs/product.md`: title/class substring matching after query trimming,
case-insensitivity, blank-query restoration, preserved server order, and the
no-matches/clear-search state. This is an approved additive frontend behavior.

## Verification

- From `frontend/`, run `node --test tests/quiz-list.test.mjs`.
- Review the React view snapshot and diff to confirm existing card markup,
  actions, order, and theme are preserved.
- The repository has no bundler/browser host; Node tests do not establish
  visual correctness. Browser verification requires the full application or an
  explicitly provided host.

## Task breakdown

One implementation task: update the product spec, frontend view/model and
frontend tests together as this single independently reviewable change.

## Dependencies and blockers

None identified. Scope and breakdown are approved; the available frontend
test command provides a verification path for the view-model behavior.
