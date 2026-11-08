# Evaluation report: commit

## Result

| Field | Value |
|---|---|
| Outcome | **FAIL** |
| Mean score | 75.0/100 |
| Passed trials | 0/1 |
| Completed trials | 1/1 |
| Experiment status | completed |
| Semantic judges | 3 per eligible trial |

## Trial results

| Test case | Configuration | Trial | Score | Pass | Details |
|---|---|---:|---:|---:|---|
| single-focused-change | with-skill | 1 | 75 | No | [result.json](trials/single-focused-change/with-skill/trial-01/result.json) |

## Main failure reasons

- **single-focused-change / with-skill / trial-01:** semantic/semantic-jury: 0/3 judges voted pass; valid judge scores: [75, 75, 90]; consensus uses the median.
- **single-focused-change / with-skill / trial-01:** semantic/conventional-type-and-traceability: Deduction: the subject is a valid concise feat subject, but the required `Refs: #63` trailer was not created as a trailer. Exact commit-message evidence shows literal backslash-n characters in the body (`...tickets,\nwith...\n...\n\nRefs: #63`) rather than actual line breaks. `git interpret-trailers --parse` produces no parsed trailer, so the commit does not satisfy the required traceability condition even though the worker proposed and reported the intended trailer text.
- **single-focused-change / with-skill / trial-01:** semantic/conventional-type-and-traceability: Deduction of 25 points. The commit has the correct `feat(ticket):` type and a concise imperative subject, and the text `Refs: #63` is present. However, observable commit-message bytes show that the worker passed literal `\\n` characters in the body, so `Refs: #63` is not on its own final body line and therefore is not a valid Git trailer as required.
- **single-focused-change / with-skill / trial-01:** semantic/conventional-type-and-traceability: The commit subject has the required feat type, is concise, and uses an imperative description: `feat(ticket): Show priority as a coloured badge`. However, the recorded commit message contains literal backslash-n characters in the body, as shown by `git log -1 --format=fuller`, so `Refs: #63` is embedded in a single malformed body line rather than being a separate valid trailer. The commit text does mention Issue #63, so partial credit is awarded for type and subject, with 10 points deducted for the malformed trailer.

## Detailed evidence

Open `trials/` for each disposable workspace, worker trace, Git evidence, and configured grader outputs. `experiment.json` contains the complete machine-readable experiment data.
