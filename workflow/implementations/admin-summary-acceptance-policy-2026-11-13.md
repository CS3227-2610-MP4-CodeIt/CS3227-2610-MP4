# Admin summary acceptance policy — 13 November 2026 (Asia/Singapore)

Status: IMPLEMENTED; runtime verification pending available backend tooling.
Authority: explicit user approval to revise the acceptance contract on
`fix/admin-summary-live-rejection`; baseline HEAD
`455a4d2163088047b9db87f3d5c35378b58ea707` plus existing diagnostic, prompt and
token-budget worktree changes. Those changes and all historical artifacts remain.
Applied implement-task/Python guidance; no independent review claimed.

## Superseding contract and experiment interpretation

This dated record supersedes the 150-word hard acceptance threshold in
`workflow/tasks/admin-summary-response-reliability.md` and
`workflow/planning/admin-summary-response-reliability.md` for current development.
Original experiment files, results and security reviews are preserved unchanged.
They remain evidence for the earlier policy, not proof of the revised contract.

User-reported controlled live observations: original prompt rejected with word_limit;
shorter prompt first succeeded then rejected with finish_length at 512 tokens;
shorter prompt at 768 tokens rejected with word_limit. The diagnostic identifies
the first rejection, not the exact response length or factual quality. The reported
58 passing Admin tests predate this revision and were not rerun successfully here.

Current generation instruction remains 100–120 words, with 768 output tokens.
Preferred presentation remains at most 150 words. Acceptance now permits up to
250 whitespace-delimited words AND 2,000 Python Unicode characters after trimming.
Full-response canary, exact stop completion, no tools and nonempty text remain
mandatory. No slicing, repair, additional calls or retry changes. The revised
151-word outcome intentionally differs from the original experiment.

The API still supports 1–3 questions per assignment. SQL aggregates, individual
submission privacy, model configuration, shared client and frontend are unchanged.
This is bounded presentation tolerance, not a claim of improved factual accuracy
or universal injection resistance. 768 tokens can still truncate, and either size
ceiling can still be exceeded. This step increases no provider token allowance.

## Changes and verification evidence

- summary.py: only the hard word constant changes in this step, 150 to 250.
- test_admin_summary_reliability.py: 151-word success, 250-word boundary and
  251-word failure, with short words below the character cap.
- test_admin_summary_validation.py: Unicode 250/251-word cases; existing 2,000/
  2,001-character cases and other rejection cases retained. Added three-question
  mocked integration test with four synthetic submissions: repeated attempts,
  distinct correctness, partial completion, verdict totals and aggregate-only input.
- test_admin_summary_diagnostics.py: short 251-word rejection fixture; acceptance
  at 151 and 250 words; sensitive-content and all other reason checks retained.
- specs/backend-spec.md section 7.3: generation target versus hard acceptance,
  unchanged size/completion/security requirements and supported assignment scope.

Actual checks:
- Before production edit: backend `python -m pytest -q tests/test_admin_summary_reliability.py tests/test_admin_summary_validation.py tests/test_admin_summary_diagnostics.py`
  failed before collection: pytest unavailable. No meaningful red test obtained.
- After edits: backend `python -m pytest -q tests/test_admin_summary_reliability.py tests/test_admin_summary_validation.py tests/test_admin_summary_diagnostics.py tests/test_admin.py`
  failed before collection: pytest unavailable. No tests claimed passed.
- Backend `python -m ruff format --check app/ai/summary.py tests/test_admin_summary_reliability.py tests/test_admin_summary_validation.py tests/test_admin_summary_diagnostics.py`
  and equivalent `python -m ruff check ...` failed: ruff unavailable.
- Backend `python -m mypy app` failed: mypy unavailable.
- Root `git diff --check` passed; Python 3.11 AST syntax checks passed for the
  four affected Python files. Short 251-word ASCII/Unicode fixtures were checked
  below 2,000 characters. These source checks are not supported-runtime evidence.

Pending local verification from backend (Python 3.14 environment):
`uv run --locked pytest -q tests/test_admin_summary_reliability.py tests/test_admin_summary_validation.py tests/test_admin_summary_diagnostics.py tests/test_admin.py`
`uv run --locked ruff format --check .`
`uv run --locked ruff check .`
`uv run --locked mypy app`
Then relevant full regression: `uv run --locked pytest -q`.

No live calls, existing-database changes, container actions, branch switches,
staging, commits, deployment or historical artifact edits. Temporary-database
test code was added but could not execute in this environment. Frontend recovery
and broader scalability/ranking semantics remain separate work.
