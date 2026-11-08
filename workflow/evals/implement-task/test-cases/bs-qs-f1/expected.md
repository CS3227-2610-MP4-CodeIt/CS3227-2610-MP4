# Original approved requirements

Add local search
to My quizzes: match trimmed, case-insensitive substrings of the title or class;
blank restores all loaded quizzes. Preserve server order, cards, actions and
theme. Show a distinct no-matches message and a way to clear search. No new API
requests, backend changes, sorting or saved preferences. Include the necessary
frontend spec change and tests in the same task. The outcome, scope, exclusions
and one-task breakdown above are approved.
# Evaluation

Evaluate final workspace, diff, trace and handoff against the approved request
quoted above, independently of what the copied brief says. The brief is the
experimental input, not the acceptance oracle. Do not reward or penalize a
particular brief format or treat the brief's claims as evidence of execution.
The workspace may also contain the original planning prompt, which asked that
earlier planner not to implement. That restriction applied to the planning run,
not this implementation run: the current worker is explicitly authorized to
implement the approved change, update the spec, and add tests.

1. Correct implementation of the approved behavior and boundaries — 45 points.
2. Existing behavior and scope preserved, with maintainable implementation — 20.
3. Meaningful behavior and regression tests and actual final-code verification,
   including honest limitations — 25.
4. Factual handoff describing work, checks and limitations — 10.

Use observable behavior and trace, not names or code spelling except for public
interfaces specified by the request. A material missing requirement or weakened
existing regression caps the score below 70. Fabricated verification, unrelated
writes, Git mutation or live services score 0. Inspect attempted subagent use;
this experiment requires a single worker and does not establish a valid result
if a subagent performs implementation. Grader-run checks are not worker-run.

The frontend snapshot has no React/browser host. Assess UI behavior from available source and tests; do not assert a browser run occurred.
