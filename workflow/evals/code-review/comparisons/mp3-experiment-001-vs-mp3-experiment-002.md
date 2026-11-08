# Comparison: code-review — mp3-experiment-001 (v1) vs mp3-experiment-002 (v2)

| Setup | v1 (mp3-experiment-001) | v2 (mp3-experiment-002) |
|---|---|---|
| Model | gpt-5.6-luna | gpt-5.6-luna |
| Reasoning effort | low | low |
| Trials per cell | 3 | 3 |

| Summary | Value |
|---|---|
| Shared cases | 2 |
| Improved (score) | 2 |
| Regressed (score) | 0 |
| Unchanged (score) | 0 |

## Case overview

| Test case | Score (v1 -> v2) | Pass rate | Mean worker time (v1 -> v2) | Time change | Billed out (v1 -> v2) | Est. cost (v1 -> v2) | Score verdict |
|---|---|---|---|---|---|---|---|
| mp3-delegated-child-boundary | 86.67 -> 89.67 (+3) | 1/3 -> 2/3 | N/A -> N/A | N/A | 14804.67 -> 13383.67 (-9.6%) | n/a | improved |
| mp3-single-agent-route | 75 -> 100 (+25) | 3/3 -> 3/3 | N/A -> N/A | N/A | 4035.67 -> 3626.33 (-10.1%) | $0.0114 -> $0.0109 (-4.7%) | improved |

## mp3-delegated-child-boundary  (mean of n=3 v1 trial(s) -> n=3 v2 trial(s))

| Axis | v1 | v2 | Change | Verdict |
|---|---|---|---|---|
| mean worker time | N/A | N/A | N/A | unknown |
| timed trials / total | 0/3 | 0/3 | — | — |
| score | 86.67 | 89.67 | +3 (+3.5%) | improved |
| det score | 98.33 | 89.67 | -8.66 (-8.8%) | regressed |
| sem score | 91.67 | 93.33 | +1.66 (+1.8%) | improved |
| pass rate | 0.33 | 0.67 | +0.33 (+100.0%) | improved |
| uncached input | 78521.33 | 79420.67 | +899.34 (+1.1%) | regressed |
| output | 14804.67 | 13383.67 | -1421 (-9.6%) | improved |
| reasoning | 2129.67 | 1669.67 | -460 (-21.6%) | improved |
| billed output | 14804.67 | 13383.67 | -1421 (-9.6%) | improved |
| est. API-equiv. cost | n/a (pricing unavailable) | n/a (pricing unavailable) | n/a | n/a |

## mp3-single-agent-route  (mean of n=3 v1 trial(s) -> n=3 v2 trial(s))

| Axis | v1 | v2 | Change | Verdict |
|---|---|---|---|---|
| mean worker time | N/A | N/A | N/A | unknown |
| timed trials / total | 0/3 | 0/3 | — | — |
| score | 75 | 100 | +25 (+33.3%) | improved |
| det score | 75 | 100 | +25 (+33.3%) | improved |
| sem score | 91.67 | 100 | +8.33 (+9.1%) | improved |
| pass rate | 1 | 1 | +0 (+0.0%) | unchanged |
| uncached input | 21461.33 | 21095.67 | -365.66 (-1.7%) | improved |
| output | 4035.67 | 3626.33 | -409.34 (-10.1%) | improved |
| reasoning | 342.67 | 330 | -12.67 (-3.7%) | improved |
| billed output | 4035.67 | 3626.33 | -409.34 (-10.1%) | improved |
| est. API-equiv. cost | $0.0114 | $0.0109 | -$0.0005 (-4.7%) | improved |

## Skill language change (v1 -> v2)

_No skill-language diff available (snapshots missing or identical)._

_Worker time is wall-clock execution, including tool calls and subagent waits; excludes setup, subsequent evidence capture and grading. Time change = v2 − v1; negative means faster. Means include all timed trials, regardless of outcome; missing timings are N/A._

_Every per-case number is a MEAN over that cell's trials; `billed output` = output (including reasoning) (lower is better on token/cost axes); `est. API-equiv. cost` is an estimate at public API list prices (2026-10-12, platform.openai.com/pricing (API list prices, Standard tier, short+long context)) — NOT actual subscription or credit spend._
