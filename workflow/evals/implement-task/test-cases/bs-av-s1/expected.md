# Original approved requirements

Add a backend
operation save_answer(record, student_id, question_id, answer). Only the owner of
an in-progress attempt may save; denied callers/states raise PermissionError.
Only question IDs q1 and q2 and integer answers 1 through 4 are valid; reject
booleans and all other values with ValueError. Validate before mutation so any
rejection leaves the entire record unchanged. Valid saves update only the answer
for that question and preserve other answers. Keep existing public behavior and
tests; include the product spec update and focused backend tests in this one
task. No frontend, network or database work. The above outcome, scope,
exclusions and one-task breakdown are approved.
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

Private acceptance results are available in the deterministic grade; interpret them alongside actual worker verification.
