# Save an answer to an in-progress attempt

**Status:** READY
**Task ID:** `backend-save-answer`

## Outcome

Add the backend operation `save_answer(record, student_id, question_id, answer)` so the owner of an in-progress attempt can save a valid answer to q1 or q2. Invalid inputs and unauthorized attempt access fail without changing any part of the record.

## Approved scope and spec delta

Update `specs/product.md` to specify that only the owner may save answers on an in-progress attempt; only question IDs `q1` and `q2` and integer answers 1 through 4 are accepted. Submitted or otherwise non-in-progress attempts and non-owners are denied. Invalid question IDs or answer values are rejected. Rejections leave the entire record unchanged.

This is a product-spec addition under Attempts and results. No other behavior change is approved.

## Implementation

- Add `save_answer(record, student_id, question_id, answer)` to `backend/attempts.py`.
- Require `record["student_id"] == student_id` and `record["status"] == "in_progress"`; otherwise raise `PermissionError`.
- Accept exactly the string question IDs `q1` and `q2` and exact integer answers 1, 2, 3, or 4. Because Python booleans are integers, explicitly reject `True` and `False`.
- Raise `ValueError` for any unsupported question ID or answer, including booleans, floats, strings, and out-of-range integers.
- Validate all conditions before mutation. On success, update only the selected entry in `record["answers"]`, preserving any other saved answers and other record fields. Return behavior is not specified by the approved contract; follow the local service convention if one exists, without changing the required mutation behavior.

## Acceptance criteria

1. An owner can save each supported answer to each supported question on an in-progress attempt.
2. Saving changes only the selected question's answer; existing answers for the other question and all other record fields remain unchanged.
3. A non-owner or any attempt not in `in_progress` raises `PermissionError` and leaves the record unchanged.
4. Unsupported question IDs and all answers other than exact integers 1 through 4 (including booleans) raise `ValueError` and leave the record unchanged.
5. Existing public behavior and tests for `open_attempt` and `read_result` remain intact.

## Focused tests

Extend `backend/test_attempts.py` to cover successful writes for q1 and q2, preservation of the other answer and unrelated fields, owner/status denials, invalid IDs, invalid answer types and values (explicitly including booleans), and full-record equality before and after every rejected save. Keep existing tests.

## Verification

From `backend/`, run the documented command:

`python3 -B -m unittest discover -s . -p 'test_*.py'`

Use synthetic in-memory records only. No frontend, network, database, dependency installation, publication, commit, or deployment work is included.
