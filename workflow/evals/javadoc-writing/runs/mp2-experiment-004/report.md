# Evaluation report: javadoc-writing

## Result

| Field | Value |
|---|---|
| Outcome | **INCOMPLETE** |
| Mean score | 65.0/100 |
| Passed trials | 0/2 |
| Completed trials | 2/24 |
| Experiment status | interrupted |
| Semantic judges | 1 per eligible trial |

## Trial results

| Test case | Configuration | Trial | Score | Pass | Details |
|---|---|---:|---:|---:|---|
| document-public-api | baseline | 1 | 65 | No | [result.json](trials/document-public-api/baseline/trial-01/result.json) |
| document-public-api | baseline | 2 | 65 | No | [result.json](trials/document-public-api/baseline/trial-02/result.json) |

## Main failure reasons

- **document-public-api / baseline / trial-01:** semantic/semantic-jury: 0/1 judges voted pass; valid judge scores: [65]; consensus uses the median.
- **document-public-api / baseline / trial-01:** semantic/getter-restraint: The trivial getDailyLimit getter is over-documented: it has a multi-line Javadoc header and a separate verbose @return block. Under the specified standard, this getter should be omitted or documented only in a one-line form. This is the sole deduction.
- **document-public-api / baseline / trial-02:** semantic/semantic-jury: 0/1 judges voted pass; valid judge scores: [65]; consensus uses the median.
- **document-public-api / baseline / trial-02:** semantic/getter-restraint: The trivial getDailyLimit getter is over-documented: it has a multi-line header plus an @return block. The expected standard permits omitting this getter documentation or using only a one-line form, so this criterion fails and the essential getter-restraint condition is not met.

## Detailed evidence

Open `trials/` for each disposable workspace, worker trace, Git evidence, and configured grader outputs. `experiment.json` contains the complete machine-readable experiment data.
