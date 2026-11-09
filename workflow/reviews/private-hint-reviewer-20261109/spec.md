# Code Review Report

## Status
- Target: current scoped worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`.
- Scope: specification and contract review of the assigned private-hint-reviewer changes; unrelated worktree changes excluded.
- Overall: FINDINGS
- Independent human review: NOT READY

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Not assessed | Outside this specialist axis. |
| Tests | Not independently run | Implementation evidence reports 194 mocked backend tests passed before a subsequent test-only change; focused test passed afterward. |
| Smoke/acceptance testing | Not verified | Live gateway, model compatibility and latency remain unverified in implementation evidence. |
| Static analysis | Not independently run | Implementation evidence reports Ruff and mypy passed. |
| Packaging/resources | Not verified | Implementation evidence reports offline build failed due to missing setuptools; gateway limits remain unverified. |
| Specification validation | Incomplete | AC-01–07 mapped below; candidate fidelity defect in SC-private-hint-1. |
| Documentation consistency | Inaccurate | Developer Guide model setup and reviewer data flow are stale; SC-private-hint-2. |

## Requirement mapping
- AC-01/07: Generator prompt, tool loop and guards remain in place; source and supplied mocked-test evidence cover guard rejection and call counts. Live generator tool compatibility remains unverified.
- AC-02: Per-call generator/reviewer model settings and default non-hint model are present; startup checks generator and global model. Gateway availability is unverified.
- AC-03: Source sends hidden expected outputs without hidden input fields, fresh nonce/canary and no tools. Candidate is altered by spotlighting before review (SC-private-hint-1); semantic injection resistance is not proven by mocks.
- AC-04/05: Strict object/key/boolean checks, negative verdict rejection and content-free fail-open paths are present; implementation evidence describes mocked cases. Classification quality and privacy against live provider behavior are not established.
- AC-06: Source implements 64 KiB, 20-second and deadline margin limits, startup independence and cancellation propagation; evidence describes mocked scenarios. Gateway limits and production latency are unverified.
- Assignment and documentation: deployment separation is unaffected; Developer Guide claims conflict with the changed model selection and protected-data flow (SC-private-hint-2).

## Next actions
- Implementation follow-up required: YES
- Edit documentation: AFTER CODE FIX
- Rerun code-review skill: AFTER FOLLOW-UP WORK
- Reason: preserve the reviewed candidate faithfully and correct setup and data-flow claims.

## Agent handoff
- Follow-up required: YES
- Current implementation/review state: two open findings; source inspection and supplied evidence only.
- Next responsible skill or human: implementation owner, then independent review.
- Priority and finding addressed: High SC-private-hint-1; Medium SC-private-hint-2.
- Exact files and line locations: `backend/app/ai/hints.py:151`; `docs/DeveloperGuide.md:88`, `:141`, `:154`.
- Required change or investigation: preserve full candidate content while retaining untrusted delimiters; update model setup and reviewer trust boundary documentation.
- Constraints and out-of-scope work: preserve generator guards, reviewer fail-open decisions and unrelated changes.
- Verification commands: run relevant backend reviewer tests and documented backend checks after changes.
- Manual checks: verify configured models and representative hint review against the live gateway when credentials are available, including tool support and latency.
- Success criteria: reviewer receives a losslessly represented guarded candidate and guide matches actual configuration and data flow.
- Documentation impact: Developer Guide update required after code correction.
- Required next rerun: code review after follow-up.
- Blocker or decision needed: live credentials and gateway access needed for live verification.

## Findings
- `SC-private-hint-1` — [High] Reviewer can receive a different candidate from the hint returned — Status: Open
- Category: acceptance contract / protected answer review
- Location: `backend/app/ai/hints.py:147-151`; `backend/app/ai/guards.py:64-71`.
- Requirement: AC-03 and backend spec §7.1 require the guarded candidate hint to be sent to the reviewer; approved bounds must not silently truncate protected content.
- Evidence: `wrap_untrusted` removes every tag matching `<untrusted-...>` from its input. Hidden outputs are escaped before wrapping to preserve literal tag-like values, but the candidate is wrapped without equivalent preservation; `run_hint` returns the original guarded hint after an accepting verdict.
- Expected / actual: the reviewer should see a faithful representation of the candidate. A candidate such as `The output is <untrusted-answer>` loses `<untrusted-answer>` in the reviewer payload while retaining it in the student-facing hint. The reviewer cannot classify the missing text, including when it equals a hidden expected output.
- Reproduction or inspection path: inspect the candidate wrapper and `wrap_untrusted` regex, or exercise a candidate and hidden expected output containing the same literal tag-like string and compare the reviewer request with the returned hint.
- Impact: the review may accept a sanitized hint while the delivered hint reveals content absent from its review; this undermines the newly required answer-disclosure check.
- Likely cause / confidence: shared spotlighting intentionally strips imitation tags but is applied to the candidate without a lossless representation; high confidence in the content mismatch, probabilistic classifier outcome.
- Fix direction and affected responsibility: encode candidate content losslessly for the reviewer while maintaining nonce-based instruction/data separation, and clearly instruct the reviewer how to interpret it.
- Tests to add/update: test tag-like and hostile delimiter candidate text against the exact guarded result and verify the reviewer receives a lossless representation.
- Documentation impact: update the reviewer description if its representation changes.
- Verification after fixing: focused reviewer tests plus relevant backend suite and review.

- `SC-private-hint-2` — [Medium] Developer Guide describes obsolete model configuration and hint data flow — Status: Open
- Category: developer documentation
- Location: `docs/DeveloperGuide.md:88`, `:141`, `:154`.
- Requirement: assignment brief requires the Developer Guide to match the product; task AC-02/03 and backend spec §7.1 define separate hint models and private reviewer access to hidden expected outputs.
- Evidence: the guide instructs operators to select a tool-capable `LLM_MODEL`, claims one model is shared by all three AI features, and describes hint context as having no hidden tests. `config.py`, `main.py` and `hints.py` now use separate generator/reviewer settings, validate the generator at startup and send hidden expected outputs to the reviewer.
- Expected / actual: setup should identify the generator model and its startup/tool requirements, the reviewer model and fail-open behavior, and distinguish generator context from reviewer-only expected outputs. Existing instructions can lead operators to configure the wrong model and misjudge protected data exposure.
- Reproduction or inspection path: compare guide lines with `backend/.env.example`, `backend/app/main.py:48` and `backend/app/ai/hints.py:142-151`.
- Impact: misleading setup can prevent startup or leave review unavailable, and the guide omits a material external data boundary.
- Likely cause / confidence: guide was not updated with the feature; high confidence.
- Fix direction and affected responsibility: update setup, environment table and context/resource design description to align with the final behavior and explicitly retain live verification limitations.
- Tests to add/update: documentation inspection against configuration and reviewer flow.
- Documentation impact: Developer Guide requires editing.
- Verification after fixing: cross-check documented defaults, startup checks, fail-open limits and data flow against code and spec.

## Positive observations
- Verdict parsing rejects duplicate keys, extra keys and non-boolean values; reviewer output is not returned directly.
- Limits, deadline margin and content-free failure messages are explicit in source and specification.

## Gaps and limitations
- Did not independently run tests or gateway calls; supplied test evidence is mocked and does not establish live availability, semantic review quality or latency.
- The supplied security matrix still labels this control as planning and describes no two-model verifier; its planning section is historical evidence rather than the approved task contract.

## Manual checks for user
- With appropriate credentials, check both configured model IDs, generator tool calls and reviewer behavior/latency through the actual gateway; do not treat mocked responses as proof of live behavior.

## Conclusion
- Follow-up is required before independent human review: preserve the reviewer candidate faithfully and update the Developer Guide.
