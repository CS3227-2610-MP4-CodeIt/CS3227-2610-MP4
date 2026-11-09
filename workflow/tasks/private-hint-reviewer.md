# private-hint-reviewer — Add a private hint classifier

Status: READY — scope and proposed failure behavior approved by user on 2026-11-09
Depends on: none
Sources: user request; [backend spec §§7.1, 8](../../specs/backend-spec.md); [classifier evidence](../live-ai/hint-generator-reviewer.md); [model selection](../live-ai/hint-model-selection.md), [outputs](../live-ai/hint-model-selection-outputs.md), [security report](../live-ai/hint-security-report.md); [security matrix DATA-01, AI-01, AI-02](../security/security-matrix.md)
Baseline: e9c2f8f; unrelated agent-scope/eval changes and untracked live-ai evidence are present.

## Outcome and scope

Add one private, tool-free reviewer call after the existing generator hint passes deterministic guards. The reviewer receives question context, hidden test expected outputs (MP4 has no reference solution field), and the guarded candidate. It returns exactly an object with boolean `is_hint` and `reveals_answer`. A valid negative verdict fails the job with a safe retry message; call, timeout, or invalid-verdict failure returns the guarded hint and records a content-free event. Never expose the reviewer response or hidden outputs in job results, errors or logs.

Use independently configured generator `qwen3-coder-next` and reviewer `nemotron3.5:30b`; preserve `llm_model` for other features. Keep generator prompt, tools, filtering, maximum three tool rounds, generator guards and public result shape unchanged. This is a single vertical slice: model configuration, reviewer, spec delta, tests and operational configuration together. No frontend, reference-solution schema, or unrelated AI behavior changes.

Spec delta proposed by user: §7.1 adds reviewer and fail-open decision; §8 narrows its existing claim that hidden tests never reach any hint context to generator context, and documents reviewer-only expected outputs and its trust boundary. The current canary rule needs an explicit reviewer exception: a reviewer canary leak is an invalid private verdict and follows fail-open; the generated hint remains guarded. The reviewer output must never be forwarded. The user approved this exception on 2026-11-09.

Decisions: The user approved bounding reviewer time and input size without silently truncating protected outputs. On oversize or insufficient remaining job time, skip review, log the reason and fail open. Choose concrete limits after checking available gateway limits and latency evidence, and ensure reviewer timeouts happen before the enclosing job timeout; preserve cancellation/shutdown semantics. Generator validation remains mandatory; reviewer unavailability must not prevent startup. The user approved the single-task breakdown and these failure behaviors on 2026-11-09.

## Acceptance and planned verification

| ID | Observable outcome | Source | Test/manual scenario and working directory |
|---|---|---|---|
| AC-01 | Existing generator prompt, tools, hidden-test filter, 3 rounds and deterministic canary/5-line/length behavior remain intact; failed or empty guard output never triggers review. | request | Backend: existing injection 422, canary, strip and bounded-loop cases plus guard failure call assertions. |
| AC-02 | Model selection uses distinct configured models; unrelated LLM calls retain global model. | request | Backend: inspect mocked request model IDs, overrides and unrelated feature behavior. |
| AC-03 | Private reviewer receives question context and hidden expected outputs, never hidden inputs unless separately approved; generator requests contain neither hidden input nor output. Candidate and other untrusted context are spotlighted with a fresh nonce, fresh canary and instruction/data separation; reviewer has no tools. | request; DATA-01, AI-01, AI-02 | Backend: synthetic unique markers, inspect every mocked call; hostile delimiter and instruction content alongside benign control. |
| AC-04 | Strict JSON object with exactly two real booleans; accept only `is_hint=true` and `reveals_answer=false`, otherwise withhold. No prose, extras, wrong types, missing fields or duplicate keys accepted. | request | Backend: cover all four boolean combinations and malformed/schema-invalid outputs. |
| AC-05 | Reviewer errors, invalid JSON/schema, canary leak, and reviewer-specific timeout fail open with a content-free log/count; generator errors retain existing behavior. | request; proposed canary exception | Backend: mock HTTP/network error, malformed content, canary and timeout; assert original guarded hint and no sensitive log, exception or response content. |
| AC-06 | Resource limits and reviewer startup behavior follow approved decisions; no implicit success claim when review was skipped. Overall job deadline and cancellation remain effective. | proposed decision | Backend: oversize data, insufficient time, missing reviewer and cancellation tests; document chosen limits and their evidence. |
| AC-07 | Tests distinguish generator requests from the extra reviewer request; bounded loop has four generator calls and one reviewer call on successful review. | request | Backend: `uv run pytest -q`; record results and limits. |

## Implementer handoff

Update the spec, implementation and tests together. Apply [implement-task](../../.agents/skills/implement-task/SKILL.md), [python-general](../../.agents/skills/python-general/SKILL.md) and relevant reviews. Verify configured model identifiers against the actual gateway when credentials are available; mocked tests cannot prove availability, classifier recall or live latency. Classifier evidence is limited to 9 bad and 7 good examples (7/9 caught and 0/7 false positives); fail-open and classifier misses leave residual leakage risk. Record checks actually run separately.
