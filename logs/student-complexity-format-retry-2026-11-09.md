# Complexity AI format reliability

- Owner: Not specified.
- Date/time: 9 November 2026; session activity observed by Codex at 11:57 Asia/Singapore.
- Scope/stage: Implementation, verification and single-agent self-review.
- Status: Implemented and self-reviewed; commit pending.
- Branch: feat/student-workbench-guidance
- Baseline: af4e3c2af5b545cf4e52ac75125fe2105c6be546
- Summary approval: approved

## Material interactions and decisions

The user requested two coupled reliability changes to `run_complexity`: a few-shot prompt and up to three same-model format retries. The user specified fresh nonce and canary per attempt, immediate failure on a canary leak, retries for malformed or empty output and call errors, and keeping retries inside the configured job timeout. The user explicitly requested single-agent work.

The live-AI prompt A/B artifact supplied the explicit JSON formatting rules and a worked code-to-JSON example. The implementation uses that tested wording. It does not add a fallback model, verifier, or ensemble.

## Work and verification

- The prompt now requires one raw JSON object, exactly four string fields, no markdown fences, and assumptions as one plain-text string.
- The retry loop creates fresh guards per attempt, returns on the first valid response, and raises the existing invalid-response `UserFacingError` after three failures. A canary leak exits immediately.
- Added integration coverage for malformed-format recovery and fresh guards. Existing cases confirm persistent invalid outputs use three calls, canary leakage uses one call, and the happy path still succeeds on its first call.
- Implementer-observed checks from `backend`: Ruff formatting, Ruff lint, mypy, and `pytest -q` all passed; 177 tests passed. Repository `git diff --check` passed.
- No live SoCLaaS call was made. Historical live-AI artifacts informed the prompt but do not verify current runtime gateway behavior.
- Single-agent self-review passed with no findings; it is not an independent review.

Evidence: `workflow/implementations/student-complexity-format-retry-20261109-01.md` and `workflow/reviews/student-complexity-format-retry-01.md`.

## Next step

Commit outcome pending; no files have been committed.
