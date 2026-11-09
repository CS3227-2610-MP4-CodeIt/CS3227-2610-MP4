# Hint feature — generator-reviewer experiment

Generated: 2026-11-09T20:41:10

Evaluates an MP3-style LLM reviewer (returns `{is_hint, reveals_answer}`) as a classifier over a labeled good/bad hint set. A reviewer is worth shipping only if it catches bad hints the deterministic guards MISS, without rejecting good hints.

Labeled set: 9 bad + 7 good hints (hint_review_fixtures.py).

## Deterministic-guard baseline (no LLM reviewer)

The existing >5-line code-strip guard neutralizes **1/9** bad hints on its own. The rest are prose leaks / short-code full solutions the guard is blind to — that gap is the only place a reviewer can add value.

## Reviewer as classifier

| Reviewer model | caught bad (recall) | false-withheld good (FP) | unparsed verdicts |
| --- | ---: | ---: | ---: |
| `qwen3-coder-next` | 6/9 | 0/7 | 0/16 |
| `nemotron3.5:30b` | 7/9 | 0/7 | 0/16 |
| `qwen3.6:35b` | 6/9 | 0/7 | 0/16 |

## Per-hint reviewer verdicts (W = withheld)

| Hint (label) | guard? | `qwen3-coder-next` | `nemotron3.5:30b` | `qwen3.6:35b` |
| --- | --- | --- | --- | --- |
| off-by-one-range (good) | blind | · | · | · |
| wrong-comparison (good) | blind | · | · | · |
| missing-empty-edge (good) | blind | · | · | · |
| tle-quadratic (good) | blind | · | · | · |
| int-vs-str (good) | blind | · | · | · |
| off-by-one-range (bad) | blind | W | W | W |
| int-vs-str (bad) | blind | W | W | W |
| wrong-comparison (bad) | blind | W | W | W |
| missing-empty-edge (bad) | blind | W | W | W |
| tle-quadratic (bad) | strips | W | W | W |
| off-by-one-range (bad) | blind | W | W | W |
| wrong-comparison (bad) | blind | · | W | · |
| int-vs-str (bad) | blind | · | · | · |
| tle-quadratic (bad) | blind | · | · | · |
| off-by-one-range (good) | blind | · | · | · |
| tle-quadratic (good) | blind | · | · | · |

Legend: W = reviewer would withhold the hint; · = reviewer lets it through; `?` = verdict did not parse (treated as fail-open / let through).
