# Evaluation report: implement-task (`experiment-010`)

**Setup:** Model <code>gpt-6-luna</code> · Reasoning effort `medium` · Trials per cell `1` · Semantic judges `3` · Status `completed` · Started `2026-11-09T02:37:40.253947+00:00`

## Result

| Outcome | Mean score | Passed | Needs review | Completed | Known worker cost subtotal | Complete worker cost |
|:---:|---:|---:|---:|---:|---:|---:|
| **PASS** | 100.0/100 | 4/4 | 0/4 | 4/4 | $0.0287 | $0.0287 |

## Worker runtime

| Test case | Config | Timed trials | Mean worker time | Min–max |
|---|---|---:|---:|---|
| needle-begin-save | with-skill | 1/1 | 1m 4.946s | 1m 4.946s–1m 4.946s |
| needle-end-save | with-skill | 1/1 | 1m 3.305s | 1m 3.305s–1m 3.305s |
| needle-middle-save | with-skill | 1/1 | 1m 9.392s | 1m 9.392s–1m 9.392s |
| needle-short-save | with-skill | 1/1 | 1m 37.571s | 1m 37.571s–1m 37.571s |

_Worker time is wall-clock execution across all turns, including tool calls and subagent waits; excludes setup, subsequent evidence capture and grading. Means and ranges include all timed trials, regardless of outcome; missing timings are N/A._

## Trials

| Test case | Config | Trial | Score | Det | Sem | Band | Pass | Worker time | Evidence |
|---|---|---:|---:|---:|---:|:--:|:--:|---:|---|
| needle-begin-save | with-skill | 1 | 100 | 100 | 100 | pass | Yes | 1m 4.946s | [result.json](trials/needle-begin-save/with-skill/trial-01/result.json) |
| needle-end-save | with-skill | 1 | 100 | 100 | 100 | pass | Yes | 1m 3.305s | [result.json](trials/needle-end-save/with-skill/trial-01/result.json) |
| needle-middle-save | with-skill | 1 | 100 | 100 | 100 | pass | Yes | 1m 9.392s | [result.json](trials/needle-middle-save/with-skill/trial-01/result.json) |
| needle-short-save | with-skill | 1 | 100 | 100 | 100 | pass | Yes | 1m 37.571s | [result.json](trials/needle-short-save/with-skill/trial-01/result.json) |

## Token usage

| Test case | Config | Uncached input | Cached input | Output | Reasoning | Billed output | Worker cost / trial |
|---|---|---:|---:|---:|---:|---:|---:|
| needle-begin-save | with-skill | 27884 | 261888 | 2815 | 291 | 2815 | $0.0068 |
| needle-end-save | with-skill | 29011 | 338944 | 2692 | 270 | 2692 | $0.0076 |
| needle-middle-save | with-skill | 28203 | 300160 | 2941 | 324 | 2941 | $0.0073 |
| needle-short-save | with-skill | 19255 | 281984 | 4504 | 311 | 4504 | $0.0070 |
| **Total (4 trials)** | — | **104353** | **1182976** | **12952** | **1196** | **12952** | **$0.0287** |

_Per-case rows are trial means (comparable only on the same model and reasoning effort); `Billed output` = output (including reasoning). `Worker cost / trial` includes worker subagents and excludes semantic judge calls. Incomplete worker pricing coverage is shown separately above. Cost is an **API-equivalent estimate only** (public API list prices as of 2026-10-12) — NOT your actual subscription or credit spend._

## Worker request pricing coverage

complete: 39 / 39 requests priced; 0 unavailable observations. Known subtotal: $0.0287. Unknown models: none.
Semantic-judge calls are excluded from worker cost and do not affect this comparison.
