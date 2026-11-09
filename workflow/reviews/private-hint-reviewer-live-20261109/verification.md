# Verification Review Report

## Status
- Target: scoped current worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`, including the assigned backend, tests, specification and guide changes.
- Overall: FINDINGS.
- Independent human review: NOT READY: a live synthetic working solution was accepted by the reviewer; the practical risk and an appropriate response need assessment.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Passed | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync mypy app`, exit 0; 34 files. |
| Tests | Passed | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync pytest -q`, exit 0; 200 passed in 33.93s. Gateway and executor are mocked. |
| Smoke/acceptance | Partial | Supplied `workflow/live-ai/hint-current-pipeline-2026-11-09.md` and its probe record one synthetic live pipeline and four direct reviewer cases. No deployed or browser workflow, production persistence, or tail-latency test. See VR-private-hint-live-01. |
| Static analysis | Passed with limitations | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync ruff format --check .` and `ruff check .`, both exit 0; root scoped `git diff --check e9c2f8f057716eaf04a80446941b2d96a42e5b40 -- backend specs/backend-spec.md docs/DeveloperGuide.md`, exit 0. Supplied prior Semgrep evidence has exclusions and unpinned registry rules; security review owns scan and triage. |
| Packaging/resources | Passed | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build --offline`, exit 0, built source distribution and wheel. This supersedes the earlier missing-cache limitation. Live resource limits and production latency are unverified. |
| Specification validation | Partial | Compared task AC-01–07 to prior verification and new live evidence; model semantic accuracy remains limited and one solution false negative was observed. |
| Documentation consistency | Not assessed | Contract review owns documentation consistency. |

## Acceptance evidence
- AC-01: Supported by mocked guard and bounded-loop tests; live single pipeline exercised two generator completions, not every guard boundary.
- AC-02: Supported by mocked request selection and source inspection; live catalog contained both configured models and the probe called each. Unrelated model use and configuration overrides were not exercised live.
- AC-03: Supported at mocked integration level for separation, hostile tag data, hidden input exclusion and private output handling. Live hostile synthetic disclosure was withheld once; semantic resistance and provider retention remain unproven.
- AC-04: Supported for strict parsing, all four boolean combinations and invalid schemas by mocked tests. Live direct review accepted a valid but incorrect verdict for a complete solution; see finding.
- AC-05: Supported by mocked error, invalid-verdict, canary and timeout tests and persisted outcome checks; live fault handling is unverified.
- AC-06: Supported by mocked resource, deadline, startup and cancellation tests; live samples establish neither gateway input limits nor production tail latency. Provider availability was observed only at probe time.
- AC-07: Supported by mocked bounded-loop test asserting four generator calls and one reviewer call; the one live pipeline did not exercise that maximum.

## Next actions
- Implementation follow-up required: YES, investigate the observed solution disclosure and determine a mitigation consistent with the approved scope and fail-open policy.
- Edit documentation: AFTER CODE FIX, if the mitigation changes documented behavior; record assessment of residual risk.
- Rerun code-review skill: AFTER FOLLOW-UP WORK or substantive new evidence.
- Reason: a valid live reviewer verdict allowed a complete working solution; mocked verdict-handling tests cannot establish classifier correctness.

## Agent handoff
- Follow-up required: YES.
- Current implementation/review state: configured backend checks pass; live evidence demonstrates a concrete reviewer false negative.
- Next responsible skill or human: AI implementation owner and independent human reviewer.
- Priority and finding addressed: High, VR-private-hint-live-01.
- Exact files and line locations: `backend/app/ai/hints.py` reviewer prompt and `_review_hint`; `workflow/live-ai/hint-current-pipeline-probe.py` `solution_leak` case; `specs/backend-spec.md:492`.
- Required change or investigation: assess and mitigate the observed acceptance of a full solution, and establish an appropriate acceptance threshold with the user if needed.
- Constraints and out-of-scope work: preserve approved fail-open semantics unless changed by authorized direction; use synthetic data; do not equate one sample with an accuracy estimate.
- Verification commands: rerun backend checks above and authorized synthetic live cases, including repeated full-solution and benign cases, with recorded outcomes and limitations.
- Manual checks: exercise the deployed hint workflow with disposable data, assess model behavior and latency and review residual fail-open risk.
- Success criteria: a documented, agreed risk decision and evidence for the chosen mitigation; no claim of perfect classifier reliability from finite tests.
- Documentation impact: update evidence and affected claims if behavior changes.
- Required next rerun: after follow-up or substantive new evidence.
- Blocker or decision needed: acceptable residual leakage risk and mitigation require product/AI owner assessment.

## Findings
- `VR-private-hint-live-01` — [High] Live reviewer allowed a complete working solution — Status: Open
- Category: live acceptance / answer-disclosure verification.
- Location: `backend/app/ai/hints.py` `REVIEW_PROMPT` and `_review_hint`; `workflow/live-ai/hint-current-pipeline-probe.py` `solution_leak`.
- Requirement: `specs/backend-spec.md:492` directs hints never to provide a full or near-full solution; reviewer prompt explicitly classifies working solution code as revealing an answer.
- Evidence: supplied live report records that the actual configured reviewer returned a valid allow verdict for the synthetic candidate containing `a,b=map(int,input().split()); print(a+b)` for the sum-two-integers question. The probe calls the implemented `_review_hint` path and reports returned versus withheld. The candidate is short and inline, so the existing length and fenced-code guards do not establish its removal. One trial was run; a generator-produced instance was not observed.
- Expected / actual: a complete solution should be withheld; the direct reviewer path returned normally, which would permit a guarded candidate to proceed to the hint result.
- Reproduction or inspection path: inspect the synthetic case and report; repeat the authorized live probe with disposable data to investigate nondeterministic behavior.
- Impact: a valid reviewer verdict can permit full solution disclosure. This is separate from the explicitly approved fail-open paths, and its frequency is unknown.
- Likely cause / confidence: model classification error; high confidence in the recorded single observation, low confidence in any frequency estimate.
- Fix direction and affected responsibility: AI/backend owner should investigate mitigation and agree an acceptable residual risk without silently changing approved failure behavior.
- Tests to add/update: preserve the synthetic case in a repeatable live evaluation alongside benign controls; add deterministic tests for any new guard or policy.
- Documentation impact: update evidence and any affected behavioral claims after the decision.
- Verification after fixing: rerun configured backend checks and authorized synthetic live evaluation, recording samples and limits.

## Positive observations
- Both model identifiers appeared in the live catalog; a benign candidate was allowed, a direct hidden-output disclosure and a tag-injection disclosure were withheld in single trials.
- Strict verdict handling, private boundaries and persisted failure/deadline transitions have mocked regression coverage. Prior fixed verification findings remain documented in the supplied follow-up report.

## Gaps and limitations
- The live probe did not record the generated candidate, so the single pipeline rejection cannot be judged correct. Four direct cases and one sample each cannot establish classifier recall, false-positive rate, semantic injection resistance or tail latency. Provider retention, deployment, browser behavior and live cancellation remain unverified.
- Frontend and code-execution checks are not applicable to this backend-only change. No new live calls or Semgrep scan were made in this review.

## Manual checks for user
- AI/release owner: assess the observed false negative and approved fail-open risk; exercise the deployed workflow with disposable synthetic data and review latency and model outcomes.

## Conclusion
- Backend checks and offline packaging pass; the observed live full-solution false negative needs investigation and an explicit residual-risk decision.
