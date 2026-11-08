# Save an answer to an in-progress attempt

**Status:** READY  
**Task ID:** `save-answer-in-progress-attempt`

## Outcome

Add `save_answer(record, student_id, question_id, answer)` to the backend attempt service. An authenticated owner may save a valid answer only while their attempt is `in_progress`. The operation changes only that question's answer and retains all other answers and record fields.

## Approved scope

- Implement the backend operation in `backend/attempts.py`.
- Update `specs/product.md` to define answer-saving behavior and its validation and authorization rules.
- Add focused unit tests in `backend/test_attempts.py`.
- Preserve the existing public behavior and tests for `open_attempt` and `read_result`.

No frontend, network, or database work.

## Contract

- Signature: `save_answer(record, student_id, question_id, answer)`.
- Permit the save only when `record["student_id"] == student_id` and `record["status"] == "in_progress"`. Any other caller or attempt state raises `PermissionError`.
- Accept only question IDs `"q1"` and `"q2"`.
- Accept only integer answers from 1 through 4. Reject `bool` explicitly, despite it being an `int` subclass in Python. Invalid question IDs and answers raise `ValueError`.
- Complete authorization and input validation before mutating `record`. Any rejection must leave the entire record unchanged.
- On success, set only `record["answers"][question_id]` to `answer`; preserve every other answer and all other record fields. Return behavior is unspecified by the approved contract; follow the service's existing conventions without changing this contract.

## Product spec delta

Extend **Attempts and results** with the approved save rule: only the owner of an in-progress attempt may save; IDs are `q1` and `q2`; choices are integers 1–4 with booleans excluded; denied owner/state checks raise `PermissionError`, invalid inputs raise `ValueError`, and rejection does not mutate the attempt. Submitted attempts remain immutable.

This makes the existing P-002 saved-answer restoration behavior concrete for saves. It does not change the existing open/reopen or result behavior.

## Acceptance criteria

1. Owner saves for both supported question IDs place the requested integer value in `answers`.
2. Saving one supported question leaves other answers and unrelated record values intact.
3. A different student and an owner with a non-`in_progress` attempt each receive `PermissionError`.
4. Unsupported question IDs and invalid answers—including `True`/`False`, non-integers, and integers outside 1–4—receive `ValueError`.
5. Tests snapshot the whole record before rejected calls and verify it is unchanged afterward, including for authorization failures.
6. Existing public behavior and tests for `open_attempt` and `read_result` continue to pass.

## Focused verification

From `backend/`, run:

```sh
python3 -B -m unittest discover -s . -p 'test_*.py'
```

## Security reference

Apply `SEC-OWN` from `workflow/security/security-matrix.md`: the backend owns the attempt-ownership check; verify that another student is denied. Extend focused tests to cover the save operation's owner and in-progress-state boundary.
