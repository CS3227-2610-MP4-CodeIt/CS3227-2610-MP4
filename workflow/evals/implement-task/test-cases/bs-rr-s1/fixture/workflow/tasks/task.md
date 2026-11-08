# optional-result-explanations — Omit explanations from result reads

Status: READY
Depends on: none
Sources: Approved request in this conversation; `specs/product.md` P-003 and P-004; `backend/attempts.py`; `backend/test_attempts.py`; `backend/README.md`.
Baseline: `1a88b6d`; worktree was clean when inspected.

## Outcome and scope

`read_result(record, student_id)` currently checks that the caller owns a submitted attempt, then returns the stored `result` object directly. Add an optional `include_explanations` boolean argument, defaulting to `True`, so existing public calls and behavior continue to work. When it is `False`, return a copy of the result with only its top-level `explanations` key omitted. Preserve every other key and value, and leave stored data unchanged. The behavior must also work when `explanations` is absent. Keep the existing owner and submitted-attempt checks unchanged; unauthorized or pre-submission reads remain denied.

Update the backend result contract in `specs/product.md` to describe the argument, default, omission behavior, copy/no-mutation guarantee, and preserved authorization boundary. Add focused unit tests in `backend/test_attempts.py`. No frontend changes or authorization-policy changes are in scope. This is one implementation and review task.

Spec delta: Approved in the user request. Refine the backend result-read contract under P-003; do not change the existing product permissions in P-003/P-004.

Decisions: `True` is the backward-compatible default. `False` omits only the top-level `explanations` key from a returned copy. Existing owner-only submitted-result access is preserved. Scope and one-task breakdown were explicitly approved by the user.

## Acceptance and planned verification

| ID | Observable outcome | Source | Test/manual scenario and working directory |
|---|---|---|---|
| AC-01 | Existing two-argument calls return the same result behavior, including explanations when present. | Approved request; P-003 | Focused unittest asserts default behavior and existing result boundary; run from `backend/`. |
| AC-02 | For an owned submitted attempt, `include_explanations=False` returns a result copy without the top-level `explanations` key, while retaining all other keys/values. | Approved request; approved backend spec delta | Focused unittest uses a result with explanations and other fields; assert returned content and that it is not the stored result object. Run from `backend/`. |
| AC-03 | False mode leaves stored result data unchanged; if the key is absent, it still returns a copy with all existing fields and does not fail or mutate stored data. | Approved request; approved backend spec delta | Focused unittest checks stored data before/after for both present and absent key cases. Run from `backend/`. |
| AC-04 | An unsubmitted attempt and a non-owner remain unable to read a result, regardless of the optional argument. | P-003, P-004; `SEC-OWN` in `workflow/security/security-matrix.md` | Focused unittest checks denial in both modes; run from `backend/`. |

## Implementer handoff

First update the result-read contract in `specs/product.md`, then implement the optional parameter and copy/omission behavior in `backend/attempts.py`, and add focused coverage in `backend/test_attempts.py`. Run `python3 -B -m unittest discover -s . -p 'test_*.py'` from `backend/`, as documented in `backend/README.md`. This task uses synthetic in-memory records only; no external services or dependency installation are needed. Record actual check results separately from this plan.
