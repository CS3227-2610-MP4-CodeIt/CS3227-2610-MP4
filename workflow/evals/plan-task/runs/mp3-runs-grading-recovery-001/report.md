# Evaluation report: plan-task (`experiment-002`)

**Setup:** Model `gpt-6-luna` · Reasoning effort `medium` · Trials per cell `3` · Semantic judges `3` · Status `interrupted` · Started `2026-10-20T04:52:40.081265+00:00`

## Result

| Outcome | Mean score | Passed | Needs review | Completed | Est. total cost |
|:---:|---:|---:|---:|---:|---:|
| **INCOMPLETE** | 100.0/100 | 12/12 | 0/12 | 12/12 | $0.0488 |

## Worker runtime

| Test case | Config | Timed trials | Mean worker time | Min–max |
|---|---|---:|---:|---|
| already-implemented | with-skill | 3/3 | 1m 19.066s | 1m 9.727s–1m 37.379s |
| awaiting-scope-approval | with-skill | 3/3 | 1m 1.042s | 1m 0.605s–1m 1.487s |
| clarify-before-planning | with-skill | 3/3 | 1m 22.555s | 1m 6.461s–1m 39.564s |
| implicit-small-change | with-skill | 3/3 | 1m 14.200s | 1m 10.118s–1m 18.010s |

_Worker time is wall-clock execution across all turns, including tool calls and subagent waits; excludes setup, subsequent evidence capture and grading. Means and ranges include all timed trials, regardless of outcome; missing timings are N/A._

## Trials

| Test case | Config | Trial | Score | Det | Sem | Band | Pass | Worker time | Evidence |
|---|---|---:|---:|---:|---:|:--:|:--:|---:|---|
| already-implemented | with-skill | 1 | 100 | 100 | — | pass | Yes | 1m 9.727s | [result.json](trials/already-implemented/with-skill/trial-01/result.json) |
| already-implemented | with-skill | 2 | 100 | 100 | — | pass | Yes | 1m 37.379s | [result.json](trials/already-implemented/with-skill/trial-02/result.json) |
| already-implemented | with-skill | 3 | 100 | 100 | — | pass | Yes | 1m 10.092s | [result.json](trials/already-implemented/with-skill/trial-03/result.json) |
| awaiting-scope-approval | with-skill | 1 | 100 | 100 | — | pass | Yes | 1m 1.487s | [result.json](trials/awaiting-scope-approval/with-skill/trial-01/result.json) |
| awaiting-scope-approval | with-skill | 2 | 100 | 100 | — | pass | Yes | 1m 0.605s | [result.json](trials/awaiting-scope-approval/with-skill/trial-02/result.json) |
| awaiting-scope-approval | with-skill | 3 | 100 | 100 | — | pass | Yes | 1m 1.034s | [result.json](trials/awaiting-scope-approval/with-skill/trial-03/result.json) |
| clarify-before-planning | with-skill | 1 | 100 | 100 | — | pass | Yes | 1m 6.461s | [result.json](trials/clarify-before-planning/with-skill/trial-01/result.json) |
| clarify-before-planning | with-skill | 2 | 100 | 100 | — | pass | Yes | 1m 21.639s | [result.json](trials/clarify-before-planning/with-skill/trial-02/result.json) |
| clarify-before-planning | with-skill | 3 | 100 | 100 | — | pass | Yes | 1m 39.564s | [result.json](trials/clarify-before-planning/with-skill/trial-03/result.json) |
| implicit-small-change | with-skill | 1 | 100 | 100 | — | pass | Yes | 1m 18.010s | [result.json](trials/implicit-small-change/with-skill/trial-01/result.json) |
| implicit-small-change | with-skill | 2 | 100 | 100 | — | pass | Yes | 1m 14.473s | [result.json](trials/implicit-small-change/with-skill/trial-02/result.json) |
| implicit-small-change | with-skill | 3 | 100 | 100 | — | pass | Yes | 1m 10.118s | [result.json](trials/implicit-small-change/with-skill/trial-03/result.json) |

## Token usage

| Test case | Config | Uncached input | Cached input | Output | Reasoning | Billed output | Est. cost |
|---|---|---:|---:|---:|---:|---:|---:|
| already-implemented | with-skill | 21156.67 | 84522.67 | 1746 | 301.67 | 2047.67 | $0.0040 |
| awaiting-scope-approval | with-skill | 26296.67 | 55338.67 | 1141.67 | 234 | 1375.67 | $0.0039 |
| clarify-before-planning | with-skill | 20733.67 | 112938.67 | 1061.33 | 252.33 | 1313.67 | $0.0039 |
| implicit-small-change | with-skill | 26838.33 | 82901.33 | 1898.67 | 152.67 | 2051.33 | $0.0045 |
| **Total (12 trials)** | — | **285076** | **1007104** | **17543** | **2822** | **20365** | **$0.0488** |

_Per-case rows are trial means (comparable only on the same model and reasoning effort); `Billed output` = output + reasoning. `Est. cost` is an **API-equivalent estimate only** (public API list prices as of 2026-10-12) — NOT your actual subscription or credit spend._
