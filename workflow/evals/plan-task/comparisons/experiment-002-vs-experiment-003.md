# Comparison: plan-task — experiment-002 (v1) vs experiment-003 (v2)

| Setup | v1 (experiment-002) | v2 (experiment-003) |
|---|---|---|
| Model | gpt-6-luna | gpt-6-luna |
| Reasoning effort | medium | medium |
| Trials per cell | 2 | 2 |

| Summary | Value |
|---|---|
| Shared cases | 7 |
| Improved (score) | 4 |
| Regressed (score) | 3 |
| Unchanged (score) | 0 |

## Case overview

| Test case | Score (v1 -> v2) | Pass rate | Mean worker time (v1 -> v2) | Time change | Billed out (v1 -> v2) | Est. cost (v1 -> v2) | Score verdict |
|---|---|---|---|---|---|---|---|
| mp3-already-implemented | 99 -> 94.5 (-4.5) | 2/2 -> 2/2 | 22.913s -> 24.499s | +1.586s (+6.9%) | 814.5 -> 783.5 (-3.8%) | $0.0024 -> $0.0020 (-16.4%) | regressed |
| mp3-awaiting-scope-approval | 96 -> 95.5 (-0.5) | 2/2 -> 2/2 | 23.194s -> 21.177s | -2.017s (-8.7%) | 678 -> 823 (+21.4%) | $0.0020 -> $0.0019 (-4.5%) | regressed |
| mp3-clarify-before-planning | 92.5 -> 94.5 (+2) | 2/2 -> 2/2 | 55.512s -> 1m 4.422s | +8.910s (+16.1%) | 1175 -> 1151 (-2.0%) | $0.0029 -> $0.0040 (+37.0%) | improved |
| mp3-implicit-small-change | 34.5 -> 45 (+10.5) | 0/2 -> 0/2 | 51.642s -> 37.802s | -13.840s (-26.8%) | 2046.5 -> 1498.5 (-26.8%) | $0.0034 -> $0.0028 (-17.0%) | improved |
| mp4-brief-answer-validation | 90.5 -> 99 (+8.5) | 2/2 -> 2/2 | 51.867s -> 36.457s | -15.410s (-29.7%) | 2243 -> 1573.5 (-29.8%) | $0.0044 -> $0.0028 (-37.3%) | improved |
| mp4-brief-quiz-search | 97 -> 95.5 (-1.5) | 2/2 -> 2/2 | 43.559s -> 39.662s | -3.897s (-8.9%) | 1886 -> 1549.5 (-17.8%) | $0.0032 -> $0.0030 (-8.2%) | regressed |
| mp4-brief-result-redaction | 98.5 -> 99 (+0.5) | 2/2 -> 2/2 | 36.778s -> 34.142s | -2.636s (-7.2%) | 1578 -> 1396.5 (-11.5%) | $0.0030 -> $0.0032 (+5.6%) | improved |

## mp3-already-implemented  (mean of n=2 v1 trial(s) -> n=2 v2 trial(s))

| Axis | v1 | v2 | Change | Verdict |
|---|---|---|---|---|
| mean worker time | 22.913s | 24.499s | +1.586s (+6.9%) | regressed |
| timed trials / total | 2/2 | 2/2 | — | — |
| score | 99 | 94.5 | -4.50 (-4.5%) | regressed |
| det score | 100 | 100 | +0 (+0.0%) | unchanged |
| sem score | 99 | 94.5 | -4.50 (-4.5%) | regressed |
| pass rate | 1 | 1 | +0 (+0.0%) | unchanged |
| uncached input | 13654 | 8362 | -5292 (-38.8%) | improved |
| output | 814.5 | 783.5 | -31 (-3.8%) | improved |
| reasoning | 273.5 | 181.5 | -92 (-33.6%) | improved |
| billed output | 814.5 | 783.5 | -31 (-3.8%) | improved |
| est. API-equiv. cost | $0.0024 | $0.0020 | -$0.0004 (-16.4%) | improved |

## mp3-awaiting-scope-approval  (mean of n=2 v1 trial(s) -> n=2 v2 trial(s))

| Axis | v1 | v2 | Change | Verdict |
|---|---|---|---|---|
| mean worker time | 23.194s | 21.177s | -2.017s (-8.7%) | improved |
| timed trials / total | 2/2 | 2/2 | — | — |
| score | 96 | 95.5 | -0.50 (-0.5%) | regressed |
| det score | 100 | 100 | +0 (+0.0%) | unchanged |
| sem score | 96 | 95.5 | -0.50 (-0.5%) | regressed |
| pass rate | 1 | 1 | +0 (+0.0%) | unchanged |
| uncached input | 8520 | 10245 | +1725 (+20.2%) | regressed |
| output | 678 | 823 | +145 (+21.4%) | regressed |
| reasoning | 48 | 160.5 | +112.50 (+234.4%) | regressed |
| billed output | 678 | 823 | +145 (+21.4%) | regressed |
| est. API-equiv. cost | $0.0020 | $0.0019 | -$0.0001 (-4.5%) | improved |

## mp3-clarify-before-planning  (mean of n=2 v1 trial(s) -> n=2 v2 trial(s))

| Axis | v1 | v2 | Change | Verdict |
|---|---|---|---|---|
| mean worker time | 55.512s | 1m 4.422s | +8.910s (+16.1%) | regressed |
| timed trials / total | 2/2 | 2/2 | — | — |
| score | 92.5 | 94.5 | +2 (+2.2%) | improved |
| det score | 100 | 100 | +0 (+0.0%) | unchanged |
| sem score | 92.5 | 94.5 | +2 (+2.2%) | improved |
| pass rate | 1 | 1 | +0 (+0.0%) | unchanged |
| uncached input | 10045 | 19565 | +9520 (+94.8%) | regressed |
| output | 1175 | 1151 | -24 (-2.0%) | improved |
| reasoning | 163.5 | 186.5 | +23 (+14.1%) | regressed |
| billed output | 1175 | 1151 | -24 (-2.0%) | improved |
| est. API-equiv. cost | $0.0029 | $0.0040 | +$0.0011 (+37.0%) | regressed |

## mp3-implicit-small-change  (mean of n=2 v1 trial(s) -> n=2 v2 trial(s))

| Axis | v1 | v2 | Change | Verdict |
|---|---|---|---|---|
| mean worker time | 51.642s | 37.802s | -13.840s (-26.8%) | improved |
| timed trials / total | 2/2 | 2/2 | — | — |
| score | 34.5 | 45 | +10.50 (+30.4%) | improved |
| det score | 34.5 | 45 | +10.50 (+30.4%) | improved |
| sem score | 47 | 91 | +44 (+93.6%) | improved |
| pass rate | 0 | 0 | +0 | unchanged |
| uncached input | 12513 | 11760 | -753 (-6.0%) | improved |
| output | 2046.5 | 1498.5 | -548 (-26.8%) | improved |
| reasoning | 69 | 85 | +16 (+23.2%) | regressed |
| billed output | 2046.5 | 1498.5 | -548 (-26.8%) | improved |
| est. API-equiv. cost | $0.0034 | $0.0028 | -$0.0006 (-17.0%) | improved |

## mp4-brief-answer-validation  (mean of n=2 v1 trial(s) -> n=2 v2 trial(s))

| Axis | v1 | v2 | Change | Verdict |
|---|---|---|---|---|
| mean worker time | 51.867s | 36.457s | -15.410s (-29.7%) | improved |
| timed trials / total | 2/2 | 2/2 | — | — |
| score | 90.5 | 99 | +8.50 (+9.4%) | improved |
| sem score | 90.5 | 99 | +8.50 (+9.4%) | improved |
| pass rate | 1 | 1 | +0 (+0.0%) | unchanged |
| uncached input | 18710 | 12219.5 | -6490.50 (-34.7%) | improved |
| output | 2243 | 1573.5 | -669.50 (-29.8%) | improved |
| reasoning | 317.5 | 207.5 | -110 (-34.6%) | improved |
| billed output | 2243 | 1573.5 | -669.50 (-29.8%) | improved |
| est. API-equiv. cost | $0.0044 | $0.0028 | -$0.0016 (-37.3%) | improved |

## mp4-brief-quiz-search  (mean of n=2 v1 trial(s) -> n=2 v2 trial(s))

| Axis | v1 | v2 | Change | Verdict |
|---|---|---|---|---|
| mean worker time | 43.559s | 39.662s | -3.897s (-8.9%) | improved |
| timed trials / total | 2/2 | 2/2 | — | — |
| score | 97 | 95.5 | -1.50 (-1.5%) | regressed |
| sem score | 97 | 95.5 | -1.50 (-1.5%) | regressed |
| pass rate | 1 | 1 | +0 (+0.0%) | unchanged |
| uncached input | 13388 | 12534.5 | -853.50 (-6.4%) | improved |
| output | 1886 | 1549.5 | -336.50 (-17.8%) | improved |
| reasoning | 115.5 | 179 | +63.50 (+55.0%) | regressed |
| billed output | 1886 | 1549.5 | -336.50 (-17.8%) | improved |
| est. API-equiv. cost | $0.0032 | $0.0030 | -$0.0003 (-8.2%) | improved |

## mp4-brief-result-redaction  (mean of n=2 v1 trial(s) -> n=2 v2 trial(s))

| Axis | v1 | v2 | Change | Verdict |
|---|---|---|---|---|
| mean worker time | 36.778s | 34.142s | -2.636s (-7.2%) | improved |
| timed trials / total | 2/2 | 2/2 | — | — |
| score | 98.5 | 99 | +0.50 (+0.5%) | improved |
| sem score | 98.5 | 99 | +0.50 (+0.5%) | improved |
| pass rate | 1 | 1 | +0 (+0.0%) | unchanged |
| uncached input | 12415.5 | 15396 | +2980.50 (+24.0%) | regressed |
| output | 1578 | 1396.5 | -181.50 (-11.5%) | improved |
| reasoning | 211 | 137.5 | -73.50 (-34.8%) | improved |
| billed output | 1578 | 1396.5 | -181.50 (-11.5%) | improved |
| est. API-equiv. cost | $0.0030 | $0.0032 | +$0.0002 (+5.6%) | regressed |

## Skill language change (v1 -> v2)

```diff
--- v1/SKILL.md
+++ v2/SKILL.md
@@ -40,8 +40,8 @@
 6. Present each task's outcome and blockers; confirm scope, exclusions and
    granularity with the user. Wait for explicit approval of the task breakdown
    before `READY`; reuse approval only for an unchanged breakdown.
-   Before writing or revising briefs, read
-   [task-brief.md](references/task-brief.md).
+   Choose the brief's structure and details for the task; include the
+   information the implementer needs to work and verify the outcome.
    Write one self-contained brief per coding task to `workflow/tasks/<task-id>.md`;
    revise matching tasks in place and preserve unrelated drafts.
 
```

_Worker time is wall-clock execution, including tool calls and subagent waits; excludes setup, subsequent evidence capture and grading. Time change = v2 − v1; negative means faster. Means include all timed trials, regardless of outcome; missing timings are N/A._

_Every per-case number is a MEAN over that cell's trials; `billed output` = output (including reasoning) (lower is better on token/cost axes); `est. API-equiv. cost` is an estimate at public API list prices (2026-10-12, platform.openai.com/pricing (API list prices, Standard tier, short+long context)) — NOT actual subscription or credit spend._
