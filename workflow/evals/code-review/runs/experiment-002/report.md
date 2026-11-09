# Evaluation report: code-review (`experiment-002`)

**Setup:** Model <code>gpt-6-luna</code> · Reasoning effort `medium` · Trials per cell `3` · Semantic judges `3` · Status `completed` · Started `2026-11-09T07:21:28.675735+00:00`

## Result

| Outcome | Mean score | Passed | Needs review | Completed | Known worker cost subtotal | Complete worker cost |
|:---:|---:|---:|---:|---:|---:|---:|
| **PASS** | 99.33/100 | 6/6 | 0/6 | 6/6 | $0.0423 | $0.0423 |

## Worker runtime

| Test case | Config | Timed trials | Mean worker time | Min–max |
|---|---|---:|---:|---|
| pd-review-authorization | with-skill | 3/3 | 1m 34.947s | 1m 18.374s–1m 53.780s |
| pd-review-validation | with-skill | 3/3 | 1m 42.744s | 1m 25.545s–2m 9.211s |

_Worker time is wall-clock execution across all turns, including tool calls and subagent waits; excludes setup, subsequent evidence capture and grading. Means and ranges include all timed trials, regardless of outcome; missing timings are N/A._

## Trials

| Test case | Config | Trial | Score | Det | Sem | Band | Pass | Worker time | Evidence |
|---|---|---:|---:|---:|---:|:--:|:--:|---:|---|
| pd-review-authorization | with-skill | 1 | 100 | 100 | 100 | pass | Yes | 1m 53.780s | [result.json](trials/pd-review-authorization/with-skill/trial-01/result.json) |
| pd-review-authorization | with-skill | 2 | 97 | 100 | 97 | pass | Yes | 1m 32.686s | [result.json](trials/pd-review-authorization/with-skill/trial-02/result.json) |
| pd-review-authorization | with-skill | 3 | 100 | 100 | 100 | pass | Yes | 1m 18.374s | [result.json](trials/pd-review-authorization/with-skill/trial-03/result.json) |
| pd-review-validation | with-skill | 1 | 99 | 100 | 99 | pass | Yes | 2m 9.211s | [result.json](trials/pd-review-validation/with-skill/trial-01/result.json) |
| pd-review-validation | with-skill | 2 | 100 | 100 | 100 | pass | Yes | 1m 33.475s | [result.json](trials/pd-review-validation/with-skill/trial-02/result.json) |
| pd-review-validation | with-skill | 3 | 100 | 100 | 100 | pass | Yes | 1m 25.545s | [result.json](trials/pd-review-validation/with-skill/trial-03/result.json) |

## Findings

- **pd-review-authorization / with-skill / trial-02** (`PASS, score 97`): semantic/contract_scope_and_honesty: Uses the stated fixed target and contract, reports the test result and unexecuted reproduction distinctly, and records unavailable static analysis and integration checks as limitations. Deducted 2 points because the documentation-consistency claim is not specifically evidenced in the report.
- **pd-review-authorization / with-skill / trial-02** (`PASS, score 97`): semantic/actionable_report: Provides a review report with finding ID, location, expected versus actual behavior, impact, fix direction, follow-up ownership, regression coverage, and verification command. Deducted 1 point for the unsupported documentation-consistency assertion.
- **pd-review-authorization / with-skill / trial-02** (`PASS, score 97`): semantic/contract_scope_checks: Correctly limits review to the fixed product target, assesses the contract, avoids unrelated findings, and reports the non-owner reproduction as unrun. The report labels smoke/acceptance testing as failed based on contract inspection, which blurs an observed test failure with an inferred behavior; it also says no manual checks remain while follow-up verification is still needed. No evidence of source/test modification or Git mutation; the sole untracked change is the requested review report.
- **pd-review-authorization / with-skill / trial-02** (`PASS, score 97`): semantic/actionable_report: Provides a detailed review with stable finding ID, location, requirement, evidence, expected versus actual behavior, impact, fix direction, regression-test suggestion, verification command, follow-up owner, and limitations. Minor deductions for inconsistent manual-check language and a few report presentation issues.
- **pd-review-validation / with-skill / trial-01** (`PASS, score 99`): semantic/material_defect: The review correctly identifies that `isinstance(True, int)` passes validation and `True` is stored, contrary to the spec. However, the report also claims the unit tests passed and compilation was exercised. The trace contains no test or compilation command, so this is an invented execution result and triggers the complete-disqualifier gate.
- **pd-review-validation / with-skill / trial-01** (`PASS, score 99`): semantic/test_gap_and_regression: The report correctly notes that existing tests omit booleans and preservation of state, and proposes a test asserting `True` raises `ValueError` without mutation. Score is zero under the invented-execution-results disqualifier.
- **pd-review-validation / with-skill / trial-01** (`PASS, score 99`): semantic/contract_scope_checks: The report accurately describes the contract and fixed target scope and acknowledges the Semgrep limitation. Its claims that tests passed and compilation was exercised are unsupported by the trace. Score is zero under the disqualifier.
- **pd-review-validation / with-skill / trial-01** (`PASS, score 99`): semantic/actionable_report: The report gives a concrete reproduction, impact, fix direction, test proposal, owner, and follow-up. Those merits do not override the disqualifier for claiming unobserved test execution.

## Token usage

| Test case | Config | Uncached input | Cached input | Output | Reasoning | Billed output | Worker cost / trial |
|---|---|---:|---:|---:|---:|---:|---:|
| pd-review-authorization | with-skill | 26214 | 194858.67 | 3027.67 | 372.33 | 3027.67 | $0.0061 |
| pd-review-validation | with-skill | 39813 | 206762.67 | 3916.33 | 755.67 | 3916.33 | $0.0080 |
| **Total (6 trials)** | — | **198081** | **1204864** | **20832** | **3384** | **20832** | **$0.0423** |

_Per-case rows are trial means (comparable only on the same model and reasoning effort); `Billed output` = output (including reasoning). `Worker cost / trial` includes worker subagents and excludes semantic judge calls. Incomplete worker pricing coverage is shown separately above. Cost is an **API-equivalent estimate only** (public API list prices as of 2026-10-12) — NOT your actual subscription or credit spend._

## Worker request pricing coverage

complete: 58 / 58 requests priced; 0 unavailable observations. Known subtotal: $0.0423. Unknown models: none.
Semantic-judge calls are excluded from worker cost and do not affect this comparison.
