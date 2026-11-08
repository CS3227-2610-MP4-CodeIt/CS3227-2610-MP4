# Optional explanation omission when reading a result

Status: READY

## Outcome

Add an optional `include_explanations` boolean parameter to the backend
`read_result(record, student_id, include_explanations=True)` function. Its
default preserves existing calls and behavior. When a submitted attempt's owner
passes `False`, return a copy of the result mapping with its top-level
`explanations` entry omitted. Keep all other entries and values intact, and do
not mutate the result stored on the record. This must also work when the key is
absent. When `True`, preserve the existing behavior and returned result.

## Scope

- Update the backend result-reading behavior and its contract in
  `specs/product.md`.
- Add focused tests in `backend/test_attempts.py` for the default behavior,
  omission of the key while preserving other result entries, stored-data
  immutability, absence of the key, and access restrictions.
- Preserve the current public call form `read_result(record, student_id)` and
  existing tests.

## Exclusions

- No frontend changes.
- No change to authorization policy: only the owner of a submitted attempt may
  read its result; non-owners and attempts not yet submitted remain denied.
- No changes to answer visibility, result computation, or persistence.

## Spec delta

Amend P-003 in `specs/product.md` to state that a result owner can optionally
omit top-level explanations when reading a submitted result. The default
includes explanations for backward compatibility. The existing requirement
that only after their own submission students can read their score, answer key,
and explanations remains in force, with authorization unchanged.

## Acceptance criteria

1. `read_result(record, student_id)` continues to include explanations and
   satisfies the existing result behavior.
2. `read_result(record, student_id, include_explanations=False)` is allowed
   only for the owner of a submitted attempt and returns the result content
   without the top-level `explanations` key.
3. With omission enabled, all other top-level result keys and values are
   preserved, and the record's stored result is unchanged after the call.
4. With omission enabled and no `explanations` key present, the call succeeds,
   returns an equivalent copy, and leaves stored data unchanged.
5. Non-owners and attempts that are not submitted continue to raise
   `PermissionError` for either option.
6. Existing two-argument calls and tests remain valid.

## Verification

From `backend/`, run the documented command:

```sh
python3 -B -m unittest discover -s . -p 'test_*.py'
```

Use synthetic records and results only. The focused tests should explicitly
check that the returned mapping for `False` is a distinct copy and that the
stored mapping retains its original contents.

## Security boundary

Keep the existing `SEC-OWN` control from `workflow/security/security-matrix.md`:
the backend enforces attempt ownership. Verify denial for a different student
under both explanation options. This task does not relax that control.
