# Admin summary rejection diagnostics

Status: IMPLEMENTED; runtime verification pending environment with backend tooling.

Current task authority: user request to instrument failures only, without live calls,
database changes, container restarts or Git actions. Contracts: backend spec sections
7.3, 8 and 9.1. No specification or behavior changes.

Baseline: branch `fix/admin-summary-live-rejection`, HEAD
`455a4d2163088047b9db87f3d5c35378b58ea707`; no tracked/staged changes.
Existing historical untracked paths were inventoried before editing and left untouched.

Changed paths:
- `backend/app/ai/summary.py`: warning messages containing fixed reason literals only.
- `backend/tests/test_admin_summary_diagnostics.py`: synthetic reply fixtures for eight
  rejection codes, precedence, safe logging and accepted boundaries (14 cases).
- This standalone evidence record.

Reason precedence preserves the existing order: canary, completion reason, tools,
empty text, word limit, character limit. Missing finish reason means None; empty or
arbitrary finish strings map to finish_other. No metadata values or counts are logged.
Canary exceptions are re-raised unchanged. No retries or generation settings changed.

Verification performed in PowerShell:
- Backend: `python -m pytest -q tests/test_admin_summary_diagnostics.py` before
  implementation: exit 1, pytest unavailable; no meaningful red test obtained.
- Backend: `python -m pytest -q tests/test_admin_summary_diagnostics.py tests/test_admin_summary_reliability.py tests/test_admin_summary_validation.py tests/test_admin.py`
  after implementation: exit 1, pytest unavailable; no tests collected.
- Root: AST parsing of both changed Python files passed using Python 3.11.9.
  This is syntax evidence only, not supported Python 3.14 runtime verification.
- Root: `git diff --check` passed for tracked diff.
- `python -m ruff --version` and `python -m mypy --version` failed: modules absent.
- Docker and uv unavailable through command lookup; no backend virtual environment.
- Manual scoped diff inspection: all logger arguments are fixed literals; API,
  user errors, validator predicates and their precedence preserved.

Pending supported-environment commands from backend:
`uv sync --locked`
`uv run --locked pytest -q tests/test_admin_summary_diagnostics.py tests/test_admin_summary_reliability.py tests/test_admin_summary_validation.py tests/test_admin.py`
`uv run --locked ruff format --check app/ai/summary.py tests/test_admin_summary_diagnostics.py`
`uv run --locked ruff check app/ai/summary.py tests/test_admin_summary_diagnostics.py`
`uv run --locked mypy app`

No live/provider/browser/container evidence. Actual historical rejection cannot be
recovered; a future user-run reproduction is needed. No independent review claimed.
Skills applied: implement-task, python-general and linked project standards.
