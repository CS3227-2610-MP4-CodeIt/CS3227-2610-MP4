# Complexity AI reliability implementation

- Status: IMPLEMENTED — scoped changes and verification exist; review was a
  single-agent self-review.
- Task: Improve complexity AI format reliability with a few-shot prompt and a
  bounded same-model format-retry loop.
- Baseline HEAD: `af4e3c2af5b545cf4e52ac75125fe2105c6be546`.
- Existing unrelated edits: frontend student-workbench files, frontend student
  spec, workflow agent-scope tooling and eval utilities, live-AI evidence, and
  prior workflow artifacts. Preserved without modification.
- Changed paths: `backend/app/ai/complexity.py`,
  `backend/tests/test_student.py`.

## Work

- Replaced the zero-shot prompt with explicit raw-JSON-only rules, four exact
  string fields, no extra keys, and a worked code-to-JSON example matching the
  live prompt A/B artifact.
- Added up to three same-model attempts. Every attempt generates a new nonce
  and canary. Empty, oversized, tool-using, malformed JSON and schema-invalid
  replies retry. LLM call exceptions and per-attempt timeouts retry. The
  per-attempt budget is 95% of the configured chat timeout divided across three
  attempts, leaving event-loop scheduling margin within the job timeout.
- Canary checking occurs after each response and outside retry handling, so a
  canary leak fails immediately. After three failures the existing invalid
  response `UserFacingError` is raised.
- Tests cover retry success after fenced invalid output, fresh nonce/canary,
  three attempts for persistently invalid output, and one-call fail-closed
  canary behavior. Existing happy-path test still inspects `calls[0]`.

## Verification

| Attribution | Directory and command | Result | Limits |
| --- | --- | --- | --- |
| Implementer-observed | `backend`: `.venv/bin/ruff format --check .` | Passed; 51 files formatted | Local configured environment |
| Implementer-observed | `backend`: `.venv/bin/ruff check .` | Passed | — |
| Implementer-observed | `backend`: `.venv/bin/mypy app` | Passed; 34 source files | — |
| Implementer-observed | `backend`: `.venv/bin/pytest -q` | Passed; 177 tests | Mocked LLM and executor; no live model call |
| Implementer-observed | repository root: `git diff --check` | Passed | — |

## Review and next step

- Self-review: PASS; see
  [review report](../reviews/student-complexity-format-retry-01.md).
- No human browser checks apply to this backend-only change. Live SoCLaaS
  behavior was not rerun; historic prompt A/B and model-sweep artifacts remain
  evidence, not a reproduction of this implementation.
- No commit was made. Development summary approval and commit outcome are
  pending.
