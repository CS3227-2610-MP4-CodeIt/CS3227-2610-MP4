# Evaluation report: implement-task (`experiment-003`)

**Setup:** Model <code>gpt-6-luna</code> · Reasoning effort `medium` · Trials per cell `2` · Semantic judges `3` · Status `completed` · Started `2026-11-08T04:22:32.426016+00:00`

## Result

| Outcome | Mean score | Passed | Needs review | Completed | Known worker cost subtotal | Complete worker cost |
|:---:|---:|---:|---:|---:|---:|---:|
| **PASS** | 95.5/100 | 4/4 | 0/4 | 4/4 | $0.0309 | $0.0309 |

## Worker runtime

| Test case | Config | Timed trials | Mean worker time | Min–max |
|---|---|---:|---:|---|
| mp4-prototype-aware-quiz-list | baseline | 2/2 | 1m 43.054s | 1m 21.456s–2m 4.652s |
| mp4-prototype-aware-quiz-list | with-skill | 2/2 | 1m 46.404s | 1m 35.667s–1m 57.141s |

_Worker time is wall-clock execution across all turns, including tool calls and subagent waits; excludes setup, subsequent evidence capture and grading. Means and ranges include all timed trials, regardless of outcome; missing timings are N/A._

## Trials

| Test case | Config | Trial | Score | Det | Sem | Band | Pass | Worker time | Evidence |
|---|---|---:|---:|---:|---:|:--:|:--:|---:|---|
| mp4-prototype-aware-quiz-list | baseline | 1 | 95 | 100 | 95 | pass | Yes | 2m 4.652s | [result.json](trials/mp4-prototype-aware-quiz-list/baseline/trial-01/result.json) |
| mp4-prototype-aware-quiz-list | baseline | 2 | 92 | 100 | 92 | pass | Yes | 1m 21.456s | [result.json](trials/mp4-prototype-aware-quiz-list/baseline/trial-02/result.json) |
| mp4-prototype-aware-quiz-list | with-skill | 1 | 99 | 100 | 99 | pass | Yes | 1m 35.667s | [result.json](trials/mp4-prototype-aware-quiz-list/with-skill/trial-01/result.json) |
| mp4-prototype-aware-quiz-list | with-skill | 2 | 96 | 100 | 96 | pass | Yes | 1m 57.141s | [result.json](trials/mp4-prototype-aware-quiz-list/with-skill/trial-02/result.json) |

## Findings

- **mp4-prototype-aware-quiz-list / baseline / trial-01** (`PASS, score 95`): semantic/test-first-work-and-regression-coverage: The existing regression test and three focused search tests ran and passed. The new tests cover trimmed case-insensitive title/class matching, literal queries, order, blank input, and immutability. The trace shows the tests were run after implementation, with no meaningful failing assertion observed beforehand, so test-first evidence is missing.
- **mp4-prototype-aware-quiz-list / baseline / trial-01** (`PASS, score 95`): semantic/sound-implementation: Filtering trims and case-folds the query, searches title and class name literally, preserves card order, and does not mutate supplied records. Browser observations confirm metadata, status-specific actions, and routes. The clear control works, though its rendered glyph appears garbled in the deterministic browser evidence.
- **mp4-prototype-aware-quiz-list / baseline / trial-01** (`PASS, score 95`): semantic/verification-and-factual-handoff: Trace evidence supports the reported passing regression test, three search tests, and node syntax check. The handoff records the changes, test evidence, evaluator-run browser acceptance, and next action. Browser acceptance is correctly not claimed as worker-run verification. Minor deduction for the garbled clear-control glyph and no additional behavioral check for the React UI beyond evaluator browser observations.
- **mp4-prototype-aware-quiz-list / baseline / trial-01** (`PASS, score 95`): semantic/test-first-regression-coverage: The new tests cover title and class matching, trim and case handling, literal queries, order, blank input, and input immutability. The existing status/order/action regression test remains intact and the trace shows it passing with the documented direct Node command. Deducted 4 points because the trace does not show a meaningful failing assertion before implementation.
- **mp4-prototype-aware-quiz-list / baseline / trial-02** (`PASS, score 92`): semantic/test-first-regression-coverage: Three focused tests cover trimmed, case-insensitive title/class search, literal matching, order, blank/no-match queries, and input immutability. The existing status/order/routes regression test remains intact and passes. Trace evidence shows the tests passing after implementation, but no meaningful failing assertion before implementation, so 8 points deducted for missing test-first evidence.
- **mp4-prototype-aware-quiz-list / baseline / trial-02** (`PASS, score 92`): semantic/test-first-work-and-regression-coverage: Added focused tests for trimmed case-insensitive title/class matching, literal queries, order preservation, blank/no-match behavior, and input immutability. The unchanged existing order/status/routes regression test passed with the documented direct Node command. Trace evidence shows checks run after implementation, with no meaningful failing assertion captured before implementation, so test-first evidence is incomplete.
- **mp4-prototype-aware-quiz-list / baseline / trial-02** (`PASS, score 92`): semantic/test-first-regression-coverage: Three focused tests cover trimmed, case-insensitive title/class search, literal matching, order, blank/no-match behavior, and input immutability. The existing order/status/action/route regression test remains intact. Trace evidence shows the documented Node commands passing after implementation, but no meaningful failing behavior assertion before implementation, so test-first evidence is incomplete.
- **mp4-prototype-aware-quiz-list / with-skill / trial-01** (`PASS, score 99`): semantic/test-first-regression-coverage: Focused tests cover trimmed/case-insensitive title and class matching, literal query text, blank restoration, no results, metadata, immutability, and existing order/status/routes regression. Handoff and trace report meaningful red failures before implementation and passing Node checks afterward. Deduction: component-level interaction is supported by grader browser observations rather than a worker-run UI test.
- **mp4-prototype-aware-quiz-list / with-skill / trial-01** (`PASS, score 99`): semantic/verification-and-handoff: Handoff records scope, acceptance evidence, exact commands and outcomes, limitations, and next action; claims align with the trace. Existing regression and focused tests passed, as did syntax and diff checks. Deduction: build, lint, typecheck, and worker-run browser checks were unavailable/not run; browser acceptance evidence is grader-run.
- **mp4-prototype-aware-quiz-list / with-skill / trial-01** (`PASS, score 99`): semantic/verification-and-factual-handoff: The handoff accurately reports the direct Node tests, syntax check, whitespace check, and unverified build/lint/browser work; trace supports the worker's check claims. It records scope, evidence, limitations, and an implicit evaluator follow-up, but does not state a clear next action as requested. No unsupported browser verification is claimed by the worker.
- **mp4-prototype-aware-quiz-list / with-skill / trial-02** (`PASS, score 96`): semantic/test-first-regression-coverage: Focused search tests and the unchanged regression test are present, and the trace shows both passing. However, the handoff claims the new tests first failed on the missing search behavior; the trace and metrics show no failed command or red test. This unsupported verification claim triggers the fabricated-verification disqualifier.
- **mp4-prototype-aware-quiz-list / with-skill / trial-02** (`PASS, score 96`): semantic/verification-and-handoff: The existing regression command and focused tests are shown passing, and the handoff records scope and the lack of worker-run browser/build checks. But its claimed red test is unsupported by the trace, which records no failed command; this is a fabricated verification claim.

## Baseline comparison

| Test case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| mp4-prototype-aware-quiz-list | 93.5 | 97.5 | +4 (+4.3%) |

## Token usage

| Test case | Config | Uncached input | Cached input | Output | Reasoning | Billed output | Worker cost / trial |
|---|---|---:|---:|---:|---:|---:|---:|
| mp4-prototype-aware-quiz-list | baseline | 29288 | 300736 | 3784 | 296.5 | 3784 | $0.0078 |
| mp4-prototype-aware-quiz-list | with-skill | 24378 | 268096 | 4988.5 | 426.5 | 4988.5 | $0.0076 |
| mp4-prototype-aware-quiz-list | **delta** | -4910 (-16.8%) | -32640 (-10.9%) | +1204.50 (+31.8%) | +130 (+43.8%) | +1204.50 (+31.8%) | -$0.0002 (-2.7%) |
| **Total (4 trials)** | — | **107332** | **1137664** | **17545** | **1446** | **17545** | **$0.0309** |

_Per-case rows are trial means (comparable only on the same model and reasoning effort); `Billed output` = output (including reasoning). `Worker cost / trial` includes worker subagents and excludes semantic judge calls. Incomplete worker pricing coverage is shown separately above. Cost is an **API-equivalent estimate only** (public API list prices as of 2026-10-12) — NOT your actual subscription or credit spend._

## Worker request pricing coverage

complete: 53 / 53 requests priced; 0 unavailable observations. Known subtotal: $0.0309. Unknown models: none.
Semantic-judge calls are excluded from worker cost and do not affect this comparison.
