# Evaluation report: javadoc-writing

## Result

| Field | Value |
|---|---|
| Outcome | **FAIL** |
| Mean score | 82.5/100 |
| Passed trials | 1/2 |
| Completed trials | 2/2 |
| Experiment status | completed |
| Semantic judges | 1 per eligible trial |

## Trial results

| Test case | Configuration | Trial | Score | Pass | Details |
|---|---|---:|---:|---:|---|
| document-public-api | baseline | 1 | 65 | No | [result.json](trials/document-public-api/baseline/trial-01/result.json) |
| document-public-api | with-skill | 1 | 100 | Yes | [result.json](trials/document-public-api/with-skill/trial-01/result.json) |

## Baseline comparison

| Test case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| document-public-api | 65.0 | 100.0 | +35.0 |

## Main failure reasons

- **document-public-api / baseline / trial-01:** semantic/semantic-jury: 0/1 judges voted pass; valid judge scores: [65]; consensus uses the median.
- **document-public-api / baseline / trial-01:** semantic/getter-restraint: getDailyLimit is a trivial getter but was given a multi-line Javadoc block containing both a description and an @return tag. The expected standard permits omitting it or using only a one-line form; this is over-documentation and fails the entire getter-restraint criterion.

## Detailed evidence

Open `trials/` for each disposable workspace, worker trace, Git evidence, and configured grader outputs. `experiment.json` contains the complete machine-readable experiment data.
