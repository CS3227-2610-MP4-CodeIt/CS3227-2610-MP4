# save-answer-validation — Save validated answers to owned attempts

Status: READY
Depends on: none
Sources: Approved request in `TASK.md`; `specs/product.md` P-002 and P-004
Baseline: `d2c25ac`; worktree clean at planning review

## Outcome and scope

`backend/attempts.py` currently exposes `open_attempt` and `read_result`; it has
no answer-saving operation. Add `save_answer(record, student_id, question_id,
answer)` for the in-memory attempt service. Only the owning student may save to
an attempt whose status is `in_progress`; other callers or attempt states raise
`PermissionError`. Accept only question IDs `q1` and `q2`, and integer answers
1 through 4. Reject booleans and every other question ID or answer with
`ValueError`. Complete all authorization/state and input checks before changing
the record, so any rejection leaves the entire record unchanged. A valid save
changes only the selected question's answer and preserves other answers.

Keep existing public behavior and tests. Update `specs/product.md` to state the
answer-save ownership, state, allowed question/answer values, and rejection
semantics. Add focused backend tests in `backend/test_attempts.py` for successful
saves, preserving other answers, ownership and state denials, valid boundaries,
booleans and invalid values, plus full-record unchanged checks after each
rejection. No frontend, network, database, or dependency work.

Spec delta: approved addition to P-002/P-004 clarifying the answer-save contract;
the request is the approval source. Decisions: IDs are the literal strings
`q1` and `q2`; answer values are integers 1–4, with booleans explicitly
excluded; rejected requests must not mutate any part of the record.

Security: covers the ownership boundary in
[`../security/security-matrix.md`](../security/security-matrix.md) `SEC-OWN`.
The current row describes attempt reads; update its boundary/control evidence
or add a write-specific row so verification explicitly covers save authorization
and denial for another student and non-in-progress states. The referenced local
OWASP threat-modeling skill was not present in the workspace; the approved
contract and targeted authorization cases define this bounded threat coverage.

## Acceptance and planned verification

| ID | Observable outcome | Source | Test/manual scenario and working directory |
|---|---|---|---|
| AC-01 | An owner can save q1 or q2 with an integer answer from 1 through 4 on an in-progress attempt. | Approved request; updated P-002/P-004 | Unit cases for both IDs and endpoint values; `backend/` |
| AC-02 | A save changes only the selected question answer and preserves all other answers and record fields. | Approved request | Seed a record with another answer and unrelated fields; assert only selected answer differs; `backend/` |
| AC-03 | A non-owner or a caller targeting an attempt in any state other than `in_progress` receives `PermissionError`. | Approved request; P-004 | Owner/state matrix; assert the complete record is unchanged; `backend/` |
| AC-04 | Unknown question IDs, non-integer answers, answers outside 1–4, and booleans receive `ValueError`. | Approved request | Include `True`/`False`, strings, floats, and out-of-range integers; assert the complete record is unchanged; `backend/` |
| AC-05 | Existing open/read behavior and tests remain intact. | P-002/P-003/P-004; existing backend tests | `python3 -B -m unittest discover -s . -p 'test_*.py'`; `backend/` |
| AC-06 | The product spec states the approved save contract, and security-matrix evidence covers write authorization. | Approved request; P-002/P-004; `SEC-OWN` | Review `specs/product.md` and `workflow/security/security-matrix.md`; repository root |

## Implementer handoff

First add the backend operation and focused unit cases, then make the matching
product spec and security-matrix evidence updates. Preserve the existing public
functions and test expectations. Use only synthetic in-memory records. Run the
backend README command from `backend/`; it exercises existing and new tests.
