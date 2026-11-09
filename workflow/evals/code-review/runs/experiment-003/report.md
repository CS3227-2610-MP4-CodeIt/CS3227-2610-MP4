# Evaluation report: code-review (`experiment-003`)

**Setup:** Model <code>gpt-6-luna</code> · Reasoning effort `medium` · Trials per cell `3` · Semantic judges `3` · Status `completed` · Started `2026-11-09T08:03:03.341688+00:00`

## Result

| Outcome | Mean score | Passed | Needs review | Completed | Known worker cost subtotal | Complete worker cost |
|:---:|---:|---:|---:|---:|---:|---:|
| **PASS** | 100.0/100 | 6/6 | 0/6 | 6/6 | $0.0300 | $0.0300 |

## Worker runtime

| Test case | Config | Timed trials | Mean worker time | Min–max |
|---|---|---:|---:|---|
| pd-review-authorization | with-skill | 3/3 | 1m 0.187s | 57.302s–1m 4.335s |
| pd-review-validation | with-skill | 3/3 | 1m 9.556s | 55.350s–1m 27.726s |

_Worker time is wall-clock execution across all turns, including tool calls and subagent waits; excludes setup, subsequent evidence capture and grading. Means and ranges include all timed trials, regardless of outcome; missing timings are N/A._

## Trials

| Test case | Config | Trial | Score | Det | Sem | Band | Pass | Worker time | Evidence |
|---|---|---:|---:|---:|---:|:--:|:--:|---:|---|
| pd-review-authorization | with-skill | 1 | 100 | 100 | 100 | pass | Yes | 58.925s | [result.json](trials/pd-review-authorization/with-skill/trial-01/result.json) |
| pd-review-authorization | with-skill | 2 | 100 | 100 | 100 | pass | Yes | 1m 4.335s | [result.json](trials/pd-review-authorization/with-skill/trial-02/result.json) |
| pd-review-authorization | with-skill | 3 | 100 | 100 | 100 | pass | Yes | 57.302s | [result.json](trials/pd-review-authorization/with-skill/trial-03/result.json) |
| pd-review-validation | with-skill | 1 | 100 | 100 | 100 | pass | Yes | 55.350s | [result.json](trials/pd-review-validation/with-skill/trial-01/result.json) |
| pd-review-validation | with-skill | 2 | 100 | 100 | 100 | pass | Yes | 1m 5.593s | [result.json](trials/pd-review-validation/with-skill/trial-02/result.json) |
| pd-review-validation | with-skill | 3 | 100 | 100 | 100 | pass | Yes | 1m 27.726s | [result.json](trials/pd-review-validation/with-skill/trial-03/result.json) |

## Token usage

| Test case | Config | Uncached input | Cached input | Output | Reasoning | Billed output | Worker cost / trial |
|---|---|---:|---:|---:|---:|---:|---:|
| pd-review-authorization | with-skill | 25651.33 | 135765.33 | 2203 | 189.67 | 2203 | $0.0050 |
| pd-review-validation | with-skill | 21417.33 | 154666.67 | 2555.67 | 333 | 2555.67 | $0.0050 |
| **Total (6 trials)** | — | **141206** | **871296** | **14276** | **1568** | **14276** | **$0.0300** |

_Per-case rows are trial means (comparable only on the same model and reasoning effort); `Billed output` = output (including reasoning). `Worker cost / trial` includes worker subagents and excludes semantic judge calls. Incomplete worker pricing coverage is shown separately above. Cost is an **API-equivalent estimate only** (public API list prices as of 2026-10-12) — NOT your actual subscription or credit spend._

## Worker request pricing coverage

complete: 35 / 35 requests priced; 0 unavailable observations. Known subtotal: $0.0300. Unknown models: none.
Semantic-judge calls are excluded from worker cost and do not affect this comparison.
