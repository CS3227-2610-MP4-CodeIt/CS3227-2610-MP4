# Backend result explanations option

Status: READY

## Outcome

Allow callers of the backend `read_result` function to omit explanations from a
submitted attempt's returned result, while keeping the current result behavior
as the default.

## Scope

- Add optional boolean parameter `include_explanations=True` to
  `backend/attempts.py` `read_result(record, student_id, ...)`.
- Keep the existing owner and submitted-status authorization checks unchanged:
  a result is readable only by the attempt owner after submission.
- With `include_explanations=True`, preserve existing behavior and returned
  result content.
- With `include_explanations=False`, return a copy of the result mapping with
  only its top-level `explanations` key omitted. Preserve every other key and
  value. Do not mutate the stored result, whether or not `explanations` exists.
- Update the backend result contract in `specs/product.md` and add focused
  standard-library `unittest` coverage in `backend/test_attempts.py`.

## Exclusions

- No frontend changes.
- No change to authorization policy or attempt ownership/status rules.
- No unrelated refactors or changes to result contents beyond omission of the
  top-level key for the opt-out call.

## Spec delta

Update P-003 / the Attempt service result contract to state that an owner may
request a submitted result without its top-level explanations field, while the
default includes explanations for backward compatibility. The existing
pre-submission and owner restrictions remain unchanged.

## Acceptance criteria

1. Existing two-argument calls to `read_result(record, student_id)` continue to
   work and include the explanations key when it is present.
2. An owner reading a submitted result with `include_explanations=False` gets a
   distinct result mapping without the top-level `explanations` key; other
   top-level fields and values are preserved.
3. The stored result remains unchanged after an opt-out read.
4. If the stored result has no `explanations` key, an opt-out read still
   succeeds, returns a copy, preserves all fields, and leaves stored data
   unchanged.
5. Non-owners and owners of unsubmitted attempts remain denied for both
   `include_explanations` values.
6. Existing public calls and tests remain valid.

## Focused verification

From `backend/`, run the documented suite:

```sh
python3 -B -m unittest discover -s . -p 'test_*.py'
```

Add tests for default inclusion/backward compatibility, opt-out key omission
and preservation of other fields, stored-data immutability, absence of the key,
and unchanged authorization boundaries for either option.

## Implementation notes

Return a shallow copy of the result mapping for the opt-out path and remove the
top-level key from that copy. Keep the default path's existing return behavior.
No additional dependency is needed.
