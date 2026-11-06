# Task 1 proposed specification delta and traceability

Date: 2026-11-06 (Asia/Singapore). Task 1 production implementation explicitly authorized after baseline review: only backend/app/ai/summary.py, plus focused supplemental tests and planning artifacts. Canonical specifications remain unchanged.

## Proposed delta to backend §§7.3 and 8

Only Admin summaries gain a response acceptance gate: text must be nonempty after trimming, completed with `finish_reason=stop`, contain no tool calls, and fit both 150 whitespace-delimited words and 2000 Python Unicode characters. Reject incomplete/invalid output rather than slicing or requesting repair. Preserve result shape, job failure shape, statistics, shared client retry policy and resource limits. Check the entire original response for canary leakage before trimming or length processing; do not persist rejected model content. Canary errors retain their existing message; new validation failures use exactly "The AI summary response was rejected. Try again." User approved this policy; canonical spec edits still require separate approval.

Malformed transport envelopes already rejected by the shared client retain existing safe failure behavior. Non-string content currently reaches a shared parser before a summary validator: investigate baseline failure/error classification, but do not modify that parser without explicit approval. Existing generic job failure may satisfy safe-failure requirements; a dedicated parser improvement is not implicitly authorized.

## Requirements-to-tests matrix

Tests: `backend/tests/test_admin_summary_reliability.py::test_summary_response_contract[case]` unless stated otherwise.

| ID | Requirement | Cases / expected outcome |
|---|---|---|
| AC-01 | Complete bounded text succeeds unchanged; preserve `{stats, summary_md}` and persisted GET status | valid, word_boundary (150), character_boundary (2000): success |
| AC-02 | Empty output never succeeds | empty, whitespace, null_content: failed |
| AC-03 | Completion metadata must indicate complete text | truncated (`length`), missing_finish_reason, unknown_finish_reason, filtered: failed |
| AC-04 | No tool execution or tool-only summaries | tool_only, text_and_tool: failed; request includes no tools |
| AC-05 | Reject excess; never silently truncate | overlong_words (151, below character cap), overlong_characters (2001, below word cap): failed |
| AC-06 | Malformed provider output fails safely | malformed_choices, malformed_content: failed with no result; generic safe failure acceptable for shared parser errors |
| AC-07 | Full-output canary leakage fails, including after character cap | canary, canary_after_limit: failed with existing rejection message |
| AC-08 | Preserve resource/security/contracts and other roles | all new cases: one mocked chat request, max_tokens=512, no tools; existing test_admin, test_guards, test_jobs, test_teacher, test_student regression suites |

New probes intentionally have no xfail markers. They assert proposed acceptance behavior so gaps remain visible as ordinary failures. Their stdout records expected/actual job status and response length without model content or canary values. All provider usage fields are synthetic, not measured consumption.

## Threat model (task-local supplement)

Existing security-matrix rows AI-01/AI-03 apply; leave shared matrix/history unchanged in this preparation stage. Assets: truthful job status, bounded Admin output, aggregate privacy and provider quota. Teachers control titles; provider output is untrusted. Flow: Admin authorization → SQL aggregates → nonce-wrapped prompt → shared mocked/provider client → proposed summary gate → existing persisted job → existing safe Markdown renderer.

| Threat | Control owner / observable check |
|---|---|
| Provider/tool output masquerades as valid summary | Summary owner: AC-02/03/04/06; no tools dispatched |
| Output exhaustion or incomplete slicing | Summary owner: AC-05; existing job timeout and AC-08 |
| Prompt/canary disclosure | Existing guard plus summary owner: AC-07 checks full output |
| Cross-role regression or broadened private context | Existing auth/context minimization tests and AC-08; no shared behavior changes |

Canaries and format checks cannot prove factual correctness or universal injection resistance. Fabrication, difficulty ranking, ties and zero-attempt interpretation remain deferred to Task 2. No new semantic verifier, HTML policy, frontend layout or fallback is included.

## Context/resource evidence and risks

Record baseline revision, commands, environment, expected/actual outcomes, test duration and call counts; distinguish blocked execution from application failure. After authorized delegation, record agent dispatches, fixed review target, correction passes and available per-agent input/cache/output/reasoning tokens using the existing workflow/evals reporting. Missing metrics are unavailable, not zero; reasoning is a subset of output. Do not run usage setup/hooks or synthetic agent trials in this stage.

Strict metadata rejection can reduce availability for providers omitting finish reasons. Boundary tests verify mechanics, not prose quality. No repair call avoids additional quota but requires manual regeneration. Generic safe errors can hide provider-shape causes; keep this limitation explicit. The exact validation error wording is approved as recorded above. Canonical spec edits and shared-file changes still require separate approval.
