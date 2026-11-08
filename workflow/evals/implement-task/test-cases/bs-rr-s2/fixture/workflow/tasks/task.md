# result-explanations-flag — Optionally omit explanations from backend results

Status: READY
Depends on: none
Sources: approved task breakdown in `TASK.md`; `specs/product.md` P-003 and P-004; `backend/attempts.py`; `backend/test_attempts.py`; `backend/README.md`
Baseline: current workspace; no baseline commit recorded

## Outcome and scope

`read_result(record, student_id)` currently checks that the caller owns a submitted attempt, then returns `record["result"]` directly. Add optional boolean `include_explanations=True`. With the default or `True`, preserve existing behavior and public calls. With `False`, return a shallow copy of the result mapping without its top-level `explanations` key; preserve all other keys and values and leave stored data unchanged. If the key is absent, still return a copy with the same contents. Keep the owner and submitted-status checks unchanged.

This one task includes the backend behavior, an additive backend spec update, and focused unit tests. No frontend changes, authorization-policy changes, dependency additions, external services, publication, commits, or deployments.

Spec delta (approved): Add to `specs/product.md` under Attempts and results that the backend result read may omit the top-level explanations field when explicitly requested; by default explanations remain included. This controls returned result presentation only and does not alter who may read a submitted result or attempt immutability.

Decisions: `include_explanations` defaults to `True` for backward compatibility. `False` returns a copy even when explanations is absent. Removal applies only to the top-level key. Scope and this one-task breakdown were explicitly approved in the request.

## Acceptance and planned verification

| ID | Observable outcome | Source | Test/manual scenario and working directory |
|---|---|---|---|
| AC-01 | Existing two-argument calls and explicit `include_explanations=True` return the existing complete result behavior, including explanations when present. | Approved request; P-003 | Focused unittest for both default and explicit True; `backend/` |
| AC-02 | For the owner of a submitted attempt, `include_explanations=False` returns all original result entries except the top-level `explanations` entry. | Approved request | Focused unittest with explanations plus multiple other keys; `backend/` |
| AC-03 | Redacting explanations does not mutate the stored result; its explanations and other entries remain unchanged after the call. | Approved request; P-003 immutability | Assert stored result equality before and after a False call; `backend/` |
| AC-04 | If the stored result lacks `explanations`, False returns an equal but distinct copy and leaves stored data unchanged. | Approved request | Focused unittest for absent key, contents and object identity; `backend/` |
| AC-05 | Non-owners and owners of unsubmitted attempts remain denied regardless of the flag value. | P-003, P-004; approved request | Focused denial cases for False and existing default behavior; `backend/` |
| AC-06 | Backend spec documents the optional flag, default inclusion, top-level omission semantics and unchanged access condition. | Approved request | Review the updated Attempts and results section in `specs/product.md`. |
| AC-07 | Existing backend tests continue to pass. | Approved request; `backend/README.md` | `python3 -B -m unittest discover -s . -p 'test_*.py'` from `backend/`. |

## Implementer handoff

Update `read_result` in `backend/attempts.py`, add focused cases in `backend/test_attempts.py`, and document the additive contract in `specs/product.md`. Run the backend unittest command from `backend/` as specified in its README. Do not change frontend code or the authorization policy.
