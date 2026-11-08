# Original approved request

The text below records the earlier planning request and its approved requirements. This implementation run should implement the approved change, not repeat the earlier planning-only instruction.

Write one coding brief for this approved task breakdown. Add a backend
operation save_answer(record, student_id, question_id, answer). Only the owner of
an in-progress attempt may save; denied callers/states raise PermissionError.
Only question IDs q1 and q2 and integer answers 1 through 4 are valid; reject
booleans and all other values with ValueError. Validate before mutation so any
rejection leaves the entire record unchanged. Valid saves update only the answer
for that question and preserve other answers. Keep existing public behavior and
tests; include the product spec update and focused backend tests in this one
task. No frontend, network or database work. The above outcome, scope,
exclusions and one-task breakdown are approved. Skip the interactive
clarification and approval rounds and write the brief directly. If you discover
a genuine blocking conflict in the supplied information, report it rather than
inventing a decision. Plan only; do not implement.
