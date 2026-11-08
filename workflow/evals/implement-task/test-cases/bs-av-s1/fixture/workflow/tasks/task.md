# save-answer-validation — Validate and save answers to in-progress attempts

Status: READY
Depends on: none
Sources: Approved request in `TASK.md`; `specs/product.md` P-002–P-004
Baseline: `3fc56d0`; clean worktree before this brief

## Outcome and scope

`backend/attempts.py` currently supports opening attempts and reading results, but has no answer-save operation. Add `save_answer(record, student_id, question_id, answer)` to the standard-library attempt service. It may mutate only an attempt owned by `student_id` whose status is `in_progress`; ownership or state denial raises `PermissionError`. Valid question IDs are exactly the strings `q1` and `q2`. Valid answers are integers 1 through 4; booleans and every other value are invalid and raise `ValueError`. Complete validation before any mutation: on every rejection the whole record remains equal to its pre-call state. A successful call changes only the selected question's answer and preserves all other answers and record fields. Keep existing public behavior and tests.

Include the approved product spec update and focused backend tests in this same task. Exclude frontend, network, and database work. No genuine blocking conflict was found in the supplied requirements or inspected backend contract.

Spec delta: Add a product requirement under Attempts and results stating that an owner may save an answer only while their attempt is in progress, only for q1/q2 with integer values 1–4 (booleans excluded), invalid answer data is rejected without record mutation, and other callers/states are denied. Ensure this contract is consistent with P-003's submitted-attempt immutability and P-004's backend ownership enforcement.

Decisions: Scope and one-task breakdown are explicitly approved in the request. Invalid question/answer data uses `ValueError`; ownership/status denial uses `PermissionError`. No precedence is specified for a call that is simultaneously unauthorized and contains invalid answer data; tests should exercise these rejection classes independently, and implementation should preserve the required atomic no-mutation property for either rejection.

## Acceptance and planned verification

| ID | Observable outcome | Source | Test/manual scenario and working directory |
|---|---|---|---|
| AC-01 | Owner saving q1 or q2 with each valid integer answer 1–4 succeeds and changes only that question's answer; existing answers and unrelated record fields are preserved. | Approved request; product spec delta | Focused `unittest` cases in `backend/test_attempts.py`; run from `backend/`. |
| AC-02 | A different student and the owner of an attempt in any state other than `in_progress` receive `PermissionError`; the record remains unchanged. | Approved request; P-002–P-004 | Focused denial cases snapshot the full record before call and compare after exception. |
| AC-03 | Unknown question IDs, answers outside 1–4, non-integer answers, and booleans raise `ValueError`; the entire record remains unchanged. | Approved request; product spec delta | Parameterized/subtest boundary cases in `backend/test_attempts.py`, including `True` and `False`, strings, and integers outside range. |
| AC-04 | Existing `open_attempt` and `read_result` public behavior and tests continue to pass. | Approved request; existing backend tests | Run `python3 -B -m unittest discover -s . -p 'test_*.py'` from `backend/`. |
| AC-05 | `specs/product.md` documents the save-answer permission, validation, and immutability contract. | Approved request; product spec delta | Review the updated Attempts and results section against AC-01–AC-03 and P-003/P-004. |

## Implementer handoff

First update `specs/product.md`, then implement the operation in `backend/attempts.py` and focused cases in `backend/test_attempts.py`. Run the backend README command from `backend/`. The security boundary is covered by existing matrix row `SEC-OWN` in `workflow/security/security-matrix.md`; extend its verification/evidence for answer saves as part of this task. The referenced OWASP threat-modeling skill file is not present in the supplied `.agents/skills` tree, so no additional matrix analysis was available; the approved acceptance contract directly covers the ownership and state denial cases. Verification is planned, not yet run; this brief does not implement the task.
