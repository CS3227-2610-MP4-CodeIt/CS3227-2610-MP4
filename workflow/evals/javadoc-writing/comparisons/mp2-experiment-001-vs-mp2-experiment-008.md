# Comparison: javadoc-writing — mp2-experiment-001 (v1) vs mp2-experiment-008 (v2)

| Setup | v1 (mp2-experiment-001) | v2 (mp2-experiment-008) |
|---|---|---|
| Model | not captured | not captured |
| Reasoning effort | not captured | not captured |
| Trials per cell | 1 | 3 |

> WARNING: model and/or reasoning effort differ between the two experiments. Score and especially token comparisons may be confounded by the model change rather than the skill edit.

| Summary | Value |
|---|---|
| Shared cases | 4 |
| Improved (score) | 0 |
| Regressed (score) | 1 |
| Unchanged (score) | 0 |

## Case overview

| Test case | Score (v1 -> v2) | Pass rate | Mean worker time (v1 -> v2) | Time change | Billed out (v1 -> v2) | Est. cost (v1 -> v2) | Score verdict |
|---|---|---|---|---|---|---|---|
| document-public-api | 100 -> 88.33 (-11.67) | 1/1 -> 1/3 | N/A -> N/A | N/A | n/a -> n/a | n/a | regressed |

## document-public-api  (mean of n=1 v1 trial(s) -> n=3 v2 trial(s))

| Axis | v1 | v2 | Change | Verdict |
|---|---|---|---|---|
| mean worker time | N/A | N/A | N/A | unknown |
| timed trials / total | 0/1 | 0/3 | — | — |
| score | 100 | 88.33 | -11.67 (-11.7%) | regressed |
| det score | 100 | 93.33 | -6.67 (-6.7%) | regressed |
| sem score | n/a | 88.33 | n/a | unknown |
| pass rate | 1 | 0.33 | -0.67 (-66.7%) | regressed |
| uncached input | n/a | n/a | n/a | unknown |
| output | n/a | n/a | n/a | unknown |
| reasoning | n/a | n/a | n/a | unknown |
| billed output | n/a | n/a | n/a | unknown |
| est. API-equiv. cost | n/a (pricing unavailable) | n/a (pricing unavailable) | n/a | n/a |

> CONFOUNDED: fixture changed (hold everything but the skill constant).

## Skill language change (v1 -> v2)

_No skill-language diff available (snapshots missing or identical)._

_Worker time is wall-clock execution, including tool calls and subagent waits; excludes setup, subsequent evidence capture and grading. Time change = v2 − v1; negative means faster. Means include all timed trials, regardless of outcome; missing timings are N/A._

_Every per-case number is a MEAN over that cell's trials; `billed output` = output (including reasoning) (lower is better on token/cost axes); `est. API-equiv. cost` is an estimate at public API list prices (2026-10-12, platform.openai.com/pricing (API list prices, Standard tier, short+long context)) — NOT actual subscription or credit spend._
