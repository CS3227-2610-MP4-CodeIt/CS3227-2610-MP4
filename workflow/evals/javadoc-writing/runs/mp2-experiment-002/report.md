# Evaluation report: javadoc-writing

## Result

| Field | Value |
|---|---|
| Outcome | **FAIL** |
| Mean score | 90.38/100 |
| Passed trials | 3/8 |
| Completed trials | 8/8 |
| Experiment status | completed |
| Semantic judges | 1 per eligible trial |

## Trial results

| Test case | Configuration | Trial | Score | Pass | Details |
|---|---|---:|---:|---:|---|
| document-public-api | baseline | 1 | 64 | No | [result.json](trials/document-public-api/baseline/trial-01/result.json) |
| document-public-api | with-skill | 1 | 74 | No | [result.json](trials/document-public-api/with-skill/trial-01/result.json) |
| negative-control-inline-comments | baseline | 1 | 85 | Yes | [result.json](trials/negative-control-inline-comments/baseline/trial-01/result.json) |
| negative-control-inline-comments | with-skill | 1 | 100 | No | [result.json](trials/negative-control-inline-comments/with-skill/trial-01/result.json) |
| no-change-when-already-documented | baseline | 1 | 100 | No | [result.json](trials/no-change-when-already-documented/baseline/trial-01/result.json) |
| no-change-when-already-documented | with-skill | 1 | 100 | No | [result.json](trials/no-change-when-already-documented/with-skill/trial-01/result.json) |
| respect-scope-boundaries | baseline | 1 | 100 | Yes | [result.json](trials/respect-scope-boundaries/baseline/trial-01/result.json) |
| respect-scope-boundaries | with-skill | 1 | 100 | Yes | [result.json](trials/respect-scope-boundaries/with-skill/trial-01/result.json) |

## Baseline comparison

| Test case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| document-public-api | 64.0 | 74.0 | +10.0 |
| negative-control-inline-comments | 85.0 | 100.0 | +15.0 |
| no-change-when-already-documented | 100.0 | 100.0 | +0.0 |
| respect-scope-boundaries | 100.0 | 100.0 | +0.0 |

## Main failure reasons

- **document-public-api / baseline / trial-01:** semantic/semantic-jury: 0/1 judges voted pass; valid judge scores: [64]; consensus uses the median.
- **document-public-api / baseline / trial-01:** semantic/correct-omission-and-restraint: The trivial getTaxRate getter is over-documented: it has a multi-line header and a verbose @return block. The stated standard permits omitting the getter or using only a one-line form, and the expected behavior explicitly requires avoiding a verbose @return block. This is a direct failure of the omission/restraint criterion and an essential pass condition.
- **document-public-api / with-skill / trial-01:** semantic/semantic-jury: 0/1 judges voted pass; valid judge scores: [74]; consensus uses the median.
- **document-public-api / with-skill / trial-01:** semantic/documentation-quality: The class, constructor, and method headers are accurate, use present-tense summaries, explain the parameters and returns, and meaningfully document applyDiscount's IllegalArgumentException without inventing contracts. The deduction is for incomplete WHAT/WHY coverage: several summaries, especially InvoiceCalculator, subtotal, and applyDiscount, describe the operation but do not clearly state the business purpose or reason the member exists beyond paraphrasing its result.
- **document-public-api / with-skill / trial-01:** semantic/correct-omission-and-restraint: The getter exemption is not respected. getTaxRate was given a multi-line header with a verbose @return block even though the project guidance permits omitting trivial getters and the expected behavior explicitly requires avoiding that over-documentation for full credit. This is unnecessary documentation churn. LineItem's class-level record-component @param documentation is restrained and relevant.
- **negative-control-inline-comments / with-skill / trial-01:** deterministic/skill-read-when-available: Expected: trace: the injected skill was read when present (baseline not applicable).
- **no-change-when-already-documented / baseline / trial-01:** deterministic/no-other-file-changed: Expected: no file other than the target was modified.
- **no-change-when-already-documented / with-skill / trial-01:** deterministic/no-other-file-changed: Expected: no file other than the target was modified.

## Detailed evidence

Open `trials/` for each disposable workspace, worker trace, Git evidence, and configured grader outputs. `experiment.json` contains the complete machine-readable experiment data.
