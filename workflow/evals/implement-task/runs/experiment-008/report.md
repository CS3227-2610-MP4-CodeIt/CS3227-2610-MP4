# Evaluation report: implement-task (`experiment-008`)

**Setup:** Model <code>gpt-6-luna</code> · Reasoning effort `medium` · Trials per cell `1` · Semantic judges `3` · Status `completed` · Started `2026-11-09T01:29:13.729201+00:00`

## Result

| Outcome | Mean score | Passed | Needs review | Completed | Known worker cost subtotal | Complete worker cost |
|:---:|---:|---:|---:|---:|---:|---:|
| **PASS** | 94.0/100 | 2/2 | 0/2 | 2/2 | $0.0630 | $0.0630 |

## Worker runtime

| Test case | Config | Timed trials | Mean worker time | Min–max |
|---|---|---:|---:|---|
| cw-crowded-quiz | with-skill | 1/1 | 5m 47.301s | 5m 47.301s–5m 47.301s |
| cw-fresh-quiz | with-skill | 1/1 | 1m 38.348s | 1m 38.348s–1m 38.348s |

_Worker time is wall-clock execution across all turns, including tool calls and subagent waits; excludes setup, subsequent evidence capture and grading. Means and ranges include all timed trials, regardless of outcome; missing timings are N/A._

## Trials

| Test case | Config | Trial | Score | Det | Sem | Band | Pass | Worker time | Evidence |
|---|---|---:|---:|---:|---:|:--:|:--:|---:|---|
| cw-crowded-quiz | with-skill | 1 | 94 | — | 94 | pass | Yes | 5m 47.301s | [result.json](trials/cw-crowded-quiz/with-skill/trial-01/result.json) |
| cw-fresh-quiz | with-skill | 1 | 94 | — | 94 | pass | Yes | 1m 38.348s | [result.json](trials/cw-fresh-quiz/with-skill/trial-01/result.json) |

## Findings

- **cw-crowded-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/approved_behavior_and_boundaries: Implements trimmed, case-insensitive substring matching on title and class, keeps filtered order, returns all loaded quizzes for blank input, and shows a distinct no-match message with a clear action. Search is derived from local component state; the diff adds no API calls, backend changes, sorting, or saved preferences. Deducted 1 point because UI interactions are supported by source inspection rather than a rendered browser check.
- **cw-crowded-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/tests_and_verification: Added helper tests for trimming, case-insensitive title/class matching, blank input, order, no matches, and card actions/fields. The handoff records direct execution of the test file passing all 6 tests and `git diff --check` passing. It honestly records `node --test` spawn EPERM failures and that browser rendering, accessibility interaction, type checking, and build were not verified. Deducted 3 points because component-level interaction and build/type checks remain unverified.
- **cw-crowded-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/behavior: Implements trimmed, case-insensitive substring matching on title or class, preserves input order, restores all items for blank input, and shows a distinct no-match message with a clear action. Filtering is local and adds no API, backend, sorting, or saved-preference behavior. Deducted 1 point because the existing card separator appears as a replacement character in the final [QuizList.tsx](trials/cw-crowded-quiz/with-skill/trial-01/workspace/frontend/QuizList.tsx) source.
- **cw-crowded-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/preservation_and_scope: Retains the existing card mapping, actions, links, and card CSS classes; the changes are limited to the frontend, product spec, tests, and handoff. The filtering helper is straightforward and derived from controlled input. Deducted 2 points for the visible separator regression.
- **cw-crowded-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/handoff: Handoff accurately reports the implementation, changed files, verification results, and limitations, and distinguishes source inspection from browser verification. Deducted 3 points because its changed-path list omits the handoff file itself and it does not mention the separator character regression.
- **cw-crowded-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/tests_and_verification: Added tests cover trimming, case-insensitive title and class matches, blank-query restoration, result order, card fields/actions, and no matches. The handoff reports six tests passed via direct Node execution and `git diff --check` passed. Deduction: the tests exercise the search helper and card model, not the React component's rendered empty state or clear interaction. The reported test-runner EPERM failures and lack of a browser host are disclosed.
- **cw-crowded-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/factual_handoff: The handoff describes the implementation, acceptance evidence, checks, failures, and browser/build limitations consistently with the captured diff and reports. Minor deduction: its changed-paths list omits the handoff file itself.
- **cw-fresh-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/implementation: Implements trimmed, case-insensitive title/class substring filtering over supplied items, preserving order; blank input restores all items. The UI shows a distinct nonblank no-match message and clear-search control. No API, backend, sorting, or preference changes are present. Deducted 2 points because no-match/clear interaction is source-reviewed rather than exercised through a UI test.
- **cw-fresh-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/tests_and_verification: Added tests for trimming, case-insensitive title/class matches, blank restoration, order, duplicate-field matching, and existing card actions/links. Handoff reports five tests passing with the isolation-disabled command and git diff --check passing. It transparently records the prescribed command's EPERM worker-spawn failure and unavailable browser host. Deducted 3 points because the React interaction itself was not tested and the available test evidence covers the view model rather than rendering.
- **cw-fresh-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/handoff: Handoff accurately summarizes scope, changed files, verification commands/results, and browser and worker-spawn limitations. Deducted 2 points because no-match and clear-search behavior are claimed from source review without direct UI test evidence.
- **cw-fresh-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/implementation: Adds local trimmed, case-insensitive substring matching on title and class, preserves input order, shows a distinct no-match message, and provides a clear-search action. Filtering uses the supplied items; no API or backend changes are present. Deducted 2 points because the UI states and interaction were source-reviewed rather than exercised in a React/browser host.
- **cw-fresh-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/tests_verification: Adds meaningful tests for matching, trimming, blank-query restoration, order, and card actions; the recorded isolated Node run passed all 5 tests, and git diff --check passed. The default Node test command failed to spawn a worker with EPERM, which the worker disclosed. Deducted 4 points because the UI empty states and clear action are not directly covered by executable component tests, and browser verification was unavailable.
- **cw-fresh-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/preservation_and_scope: Existing card fields, status-dependent actions, links, ordering, and green card styling are preserved; changes stay within the approved scope. Deducted 1 point because an empty loaded list now displays “No quizzes assigned” where the previous UI rendered an empty grid, an unrequested change to that state.
- **cw-fresh-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/tests_and_verification: Added tests for trimmed and case-insensitive matching, title/class matches, blank restoration, no matches, ordering, and card behavior. The handoff and trace record five tests passing with --test-isolation=none and git diff --check passing; the default test command failed with EPERM before assertions. Deducted 3 points because the React empty-state and clear-button behavior was source-reviewed rather than component-tested or browser-exercised.
- **cw-fresh-quiz / with-skill / trial-01** (`PASS, score 94`): semantic/handoff: Handoff accurately lists changed files, implementation evidence, checks, and the lack of browser verification. Deducted 1 point for minor character-rendering issues in the handoff text.

## Token usage

| Test case | Config | Uncached input | Cached input | Output | Reasoning | Billed output | Worker cost / trial |
|---|---|---:|---:|---:|---:|---:|---:|
| cw-crowded-quiz | with-skill | 162937 | 3038848 | 13462 | 3196 | 13462 | $0.0534 |
| cw-fresh-quiz | with-skill | 40628 | 341504 | 4310 | 495 | 4310 | $0.0096 |
| **Total (2 trials)** | — | **203565** | **3380352** | **17772** | **3691** | **17772** | **$0.0630** |

_Per-case rows are trial means (comparable only on the same model and reasoning effort); `Billed output` = output (including reasoning). `Worker cost / trial` includes worker subagents and excludes semantic judge calls. Incomplete worker pricing coverage is shown separately above. Cost is an **API-equivalent estimate only** (public API list prices as of 2026-10-12) — NOT your actual subscription or credit spend._

## Worker request pricing coverage

complete: 68 / 68 requests priced; 0 unavailable observations. Known subtotal: $0.0630. Unknown models: none.
Semantic-judge calls are excluded from worker cost and do not affect this comparison.
