# Evaluation report: plan-task (`experiment-001`)

**Setup:** Model `gpt-5.6-luna` · Reasoning effort `low` · Trials per cell `1` · Semantic judges `1` · Status `completed` · Started `2026-10-20T03:24:28.573707+00:00`

## Result

| Outcome | Mean score | Passed | Needs review | Completed | Est. total cost |
|:---:|---:|---:|---:|---:|---:|
| **FAIL** | 69.0/100 | 0/1 | 0/1 | 1/1 | $0.0128 |

## Worker runtime

| Test case | Config | Timed trials | Mean worker time | Min–max |
|---|---|---:|---:|---|
| implicit-small-change | with-skill | 1/1 | 1m 22.459s | 1m 22.459s–1m 22.459s |

_Worker time is wall-clock execution across all turns, including tool calls and subagent waits; excludes setup, subsequent evidence capture and grading. Means and ranges include all timed trials, regardless of outcome; missing timings are N/A._

## Trials

| Test case | Config | Trial | Score | Det | Sem | Band | Pass | Worker time | Evidence |
|---|---|---:|---:|---:|---:|:--:|:--:|---:|---|
| implicit-small-change | with-skill | 1 | 69 | 69 | 100 | partial | No | 1m 22.459s | [result.json](trials/implicit-small-change/with-skill/trial-01/result.json) |

## Findings

- **implicit-small-change / with-skill / trial-01** (`FAIL, score 69`): deterministic/local-references-and-baseline: [my-quizzes-empty-state.md](trials/implicit-small-change/with-skill/trial-01/workspace/workflow/tasks/my-quizzes-empty-state.md): baseline is not an initial revision

## Token usage

| Test case | Config | Uncached input | Cached input | Output | Reasoning | Billed output | Est. cost |
|---|---|---:|---:|---:|---:|---:|---:|
| implicit-small-change | with-skill | 38917 | 83712 | 2533 | 261 | 2794 | $0.0128 |

_Per-case rows are trial means (comparable only on the same model and reasoning effort); `Billed output` = output + reasoning. `Est. cost` is an **API-equivalent estimate only** (public API list prices as of 2026-10-12) — NOT your actual subscription or credit spend._
