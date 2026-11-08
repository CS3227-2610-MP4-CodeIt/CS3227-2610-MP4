# Student quiz list search

Status: READY — approved task
Owner: Eval owner
Sources: `specs/product.md`
Approved design: `frontend/prototype/selected.html`

## Outcome and scope

Implement the student quiz-list view shown in the linked approved prototype.
Add title/class search and the clear/no-results behavior in P-002 while
preserving P-001 card ordering, status actions, links and input immutability.

Allowed scope: source changes in `frontend/src/`, new focused tests under
`frontend/tests/`, and the required unique implementation handoff under
`workflow/implementations/<task-id>-<run-id>.md`. Do not change the prototype,
product contract, fixed fixture data, or existing regression test.

## Acceptance

- Search matches title or class name, case-insensitively after trimming.
- Search treats text literally and preserves the original order of matches.
- Clearing search restores all cards; no matches show the specified empty state.
- Card metadata, status labels and routes remain correct.
- The rendered UI follows the linked prototype at desktop and mobile widths.
