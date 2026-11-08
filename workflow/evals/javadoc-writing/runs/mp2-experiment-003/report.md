# Evaluation report: javadoc-writing

## Result

| Field | Value |
|---|---|
| Outcome | **FAIL** |
| Mean score | 88.75/100 |
| Passed trials | 5/8 |
| Completed trials | 8/8 |
| Experiment status | completed |
| Semantic judges | 3 per eligible trial |

## Trial results

| Test case | Configuration | Trial | Score | Pass | Details |
|---|---|---:|---:|---:|---|
| document-public-api | baseline | 1 | 65 | No | [result.json](trials/document-public-api/baseline/trial-01/result.json) |
| document-public-api | with-skill | 1 | 65 | No | [result.json](trials/document-public-api/with-skill/trial-01/result.json) |
| negative-control-inline-comments | baseline | 1 | 95 | Yes | [result.json](trials/negative-control-inline-comments/baseline/trial-01/result.json) |
| negative-control-inline-comments | with-skill | 1 | 85 | No | [result.json](trials/negative-control-inline-comments/with-skill/trial-01/result.json) |
| no-change-when-already-documented | baseline | 1 | 100 | Yes | [result.json](trials/no-change-when-already-documented/baseline/trial-01/result.json) |
| no-change-when-already-documented | with-skill | 1 | 100 | Yes | [result.json](trials/no-change-when-already-documented/with-skill/trial-01/result.json) |
| respect-scope-boundaries | baseline | 1 | 100 | Yes | [result.json](trials/respect-scope-boundaries/baseline/trial-01/result.json) |
| respect-scope-boundaries | with-skill | 1 | 100 | Yes | [result.json](trials/respect-scope-boundaries/with-skill/trial-01/result.json) |

## Baseline comparison

| Test case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| document-public-api | 65.0 | 65.0 | +0.0 |
| negative-control-inline-comments | 95.0 | 85.0 | -10.0 |
| no-change-when-already-documented | 100.0 | 100.0 | +0.0 |
| respect-scope-boundaries | 100.0 | 100.0 | +0.0 |

## Main failure reasons

- **document-public-api / baseline / trial-01:** semantic/semantic-jury: 0/3 judges voted pass; valid judge scores: [64, 71, 65]; consensus uses the median.
- **document-public-api / baseline / trial-01:** semantic/documentation-quality: The class, constructor, methods, and record components have accurate, concise Javadoc, and applyDiscount meaningfully documents both percentage parameters, its return value, and the IllegalArgumentException condition. Deduction: the first sentences generally describe WHAT the member does but do not consistently explain WHY or the member's role in the billing API; for example, subtotal and applyDiscount describe their calculations without stating the purpose those results serve. The documentation otherwise avoids line-by-line implementation restatement and does not invent parameters or exceptions.
- **document-public-api / baseline / trial-01:** semantic/correct-omission-and-restraint: The getter has a concise one-line description, but it also has a verbose @return block. The expected standard specifically permits omitting trivial getters or documenting them only in one line, and full credit requires not adding that @return block. This is unnecessary documentation churn and violates the stated restraint criterion.
- **document-public-api / baseline / trial-01:** semantic/documentation-quality: Most headers accurately describe the documented API, and applyDiscount has meaningful parameter and exception documentation. However, the total method's @return text says “the subtotal including tax” even though the method returns the invoice total, so the return description is semantically inaccurate. Several first sentences describe what the member does but do not clearly express a distinct purpose or rationale beyond the operation itself, preventing full documentation-quality credit.
- **document-public-api / baseline / trial-01:** semantic/correct-omission-and-restraint: The worker explicitly added a multi-line Javadoc block and @return tag to getTaxRate. PROJECT.md permits getters to be omitted, and the expected behaviour specifically requires avoiding a verbose @return block for this trivial getter. The billing changes otherwise show reasonable restraint, but this direct violation substantially reduces this criterion.
- **document-public-api / baseline / trial-01:** semantic/documentation-quality: The Javadoc is accurate, concise, present-tense, and avoids implementation details. The parameter descriptions and the applyDiscount @throws description are meaningful and do not invent behavior. However, the first sentences generally state only WHAT the member does, not WHY or the intended purpose as required: for example, the class, constructor, subtotal, total, and applyDiscount descriptions do not explain the business/API purpose beyond restating the operation. This warrants a deduction from the full 40 points.
- **document-public-api / baseline / trial-01:** semantic/correct-omission-and-restraint: The getter getTaxRate is explicitly exempt from full documentation by PROJECT.md and the expected behavior. The worker initially recognized this, but then added a multi-line Javadoc block with an @return tag solely to eliminate a Javadoc warning. This is the specific over-documentation the criterion warns against and is a substantial restraint violation. The other documented members are appropriately scoped.
- **document-public-api / with-skill / trial-01:** semantic/semantic-jury: 0/3 judges voted pass; valid judge scores: [65, 80, 65]; consensus uses the median.
- **document-public-api / with-skill / trial-01:** semantic/correct-omission-and-restraint: The trivial getter getTaxRate is over-documented with a multi-line Javadoc block and a verbose @return tag. The project standard permits omitting getters, and the expected behavior specifically requires that this getter not receive a verbose @return block. This is a material restraint violation and loses the full 35 points for this criterion.
- **document-public-api / with-skill / trial-01:** semantic/correct-omission-and-restraint: The getter getTaxRate should have been omitted or documented only in a one-line form under the project standard. The worker added a multi-line description plus a verbose @return block, over-documenting a trivial getter. The remaining billing documentation is appropriately scoped, but this explicit restraint requirement is not satisfied; 20 of 35 points are deducted.
- **document-public-api / with-skill / trial-01:** semantic/correct-omission-and-restraint: The trivial `getTaxRate` getter is over-documented with a multi-line header and an explicit `@return` block. The project standard permits omitting getters, and the expected behavior specifically requires avoiding a verbose getter header; this violates the restraint requirement and the essential pass condition.
- **negative-control-inline-comments / with-skill / trial-01:** semantic/semantic-jury: 1/3 judges voted pass; valid judge scores: [75, 85, 85]; consensus uses the median.
- **negative-control-inline-comments / with-skill / trial-01:** semantic/inline-comment-quality: The comment before the bounds check usefully explains why out-of-range busy-slot entries are ignored, and the scan comment clearly explains why the loop scans in order to return the first unclaimed slot. However, the comments do not explain the important marking step (`taken[slot] = true`) in WHAT/WHY terms, and there is no comment explaining that `return -1` represents the not-found case. These omissions prevent full credit for the required inline-comment coverage.
- **negative-control-inline-comments / with-skill / trial-01:** semantic/inline-comment-quality: The comments are brief and useful: one explains why out-of-range busy-slot entries are ignored, and the other explains why the scan proceeds in order to return the first unclaimed slot. However, the expected outcome specifically calls for explaining the non-obvious marking of busy slots and the `-1` not-found result. Neither `taken[slot] = true` nor the final `return -1` is commented, so the quality criterion is only partially satisfied.
- **negative-control-inline-comments / with-skill / trial-01:** semantic/inline-comment-quality: The comments are brief and useful in part: the first explains why out-of-range busy-slot entries are ignored, and the second explains why the scan proceeds in order. However, they do not explicitly explain the non-obvious marking of valid busy slots, and there is no comment explaining the `-1` result when no free slot exists. Because the expected behavior specifically calls for coverage of marking busy slots, returning the first free index, and the not-found result in WHAT/WHY terms, 15 of the 45 points are deducted.

## Detailed evidence

Open `trials/` for each disposable workspace, worker trace, Git evidence, and configured grader outputs. `experiment.json` contains the complete machine-readable experiment data.
