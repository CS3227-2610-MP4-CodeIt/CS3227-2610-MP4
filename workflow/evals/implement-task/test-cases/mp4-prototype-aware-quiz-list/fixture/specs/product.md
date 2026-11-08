# Product contract

P-001: Render the supplied student quiz records in server order. Each card
shows its title, class, question count and status. `not_started` links to the
attempt route with action `Start`; `in_progress` uses `Resume`; `submitted` uses
the results route and action `View results`. Do not mutate the supplied records.

P-002: A labelled search field filters by title or class name, case-insensitively
after trimming surrounding whitespace. Matching is literal text, not a regular
expression. Blank input restores every record in its original order. A clear
control resets a nonblank query. A nonblank query with no matches shows the
message `No quizzes match your search.`

P-003: The search field is keyboard accessible and has the accessible name
`Search quizzes`. The selected prototype controls the approved visual layout;
this contract controls behavior.
