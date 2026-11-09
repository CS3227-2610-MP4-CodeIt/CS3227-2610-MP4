# Code Review Report

## Status
- Target: scoped current worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`, including `workflow/live-ai/hint-current-pipeline-2026-11-09.md`.
- Scope: assigned private hint reviewer backend changes, tests, backend specification and Developer Guide; unrelated changes excluded.
- Overall: FAIL — two open High findings and an unresolved blocked specification axis.
- Independent human review: NOT READY; risk assessment and outstanding evidence are required.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Passed | Verification reviewer: `backend/`, `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync mypy app`, exit 0; 34 files. |
| Tests | Passed with scope limits | Verification reviewer: `backend/`, `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync pytest -q`, 200 passed; gateway and executor mocked. |
| Smoke/acceptance testing | Partial | Supplied synthetic live evidence: one pipeline and four direct reviewer cases, one trial each; no deployed or persisted production job. |
| Static analysis | Passed with limits | Verification reviewer ran backend Ruff format and lint and scoped root diff check; security reviewer ran root Semgrep, with exclusions and unpinned rules. See axis sections for exact commands and results. |
| Packaging/resources | Passed with limits | Verification reviewer: `backend/`, `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build --offline`, exit 0; live limits and production latency unverified. |
| Specification validation | Partial / BLOCKED | Contract reviewer mapped AC-01–07; classifier reliability and deployment acceptance remain unproven. |
| Documentation consistency | Inspected | Contract reviewer compared changed spec and guide with implementation and approved task. |

## Next actions
- Implementation follow-up required: YES — investigate the observed disclosure and assess mitigation with the AI/product owner.
- Edit documentation: AFTER CODE FIX if behavior or risk claims change.
- Rerun code-review skill: AFTER FOLLOW-UP WORK or substantive new evidence.
- Reason: Two independently reported High findings describe the same observed false negative; the specification axis remains blocked on risk assessment and evidence. Retained separately for attribution.

## Agent handoff
- Follow-up required: YES; full acceptance BLOCKED pending risk decision and evidence.
- Current implementation/review state: Backend checks pass within mocked scope; a synthetic complete solution was allowed in one direct live reviewer trial, not observed as a generated production hint.
- Next responsible skill or human: AI/backend implementation owner, product/risk owner and independent human reviewer.
- Priority and finding addressed: High, `SB-private-hint-live-01` and `VR-private-hint-live-01`.
- Exact files and line locations: `backend/app/ai/hints.py:21`, `backend/app/ai/hints.py:113`, `backend/app/ai/hints.py:185`, `backend/app/ai/hints.py:192`; `workflow/live-ai/hint-current-pipeline-probe.py` solution_leak case; `specs/backend-spec.md:492`.
- Required change or investigation: Assess residual risk and investigate mitigation; establish an acceptance threshold if needed and evaluate representative synthetic benign, solution, hidden-output and adversarial cases.
- Constraints and out-of-scope work: Preserve approved fail-open semantics unless authorized direction changes them; use synthetic data and do not infer accuracy from one sample.
- Verification commands: Rerun backend checks listed in the verification axis and an authorized synthetic live probe (`backend/`: `.venv/bin/python ../workflow/live-ai/hint-current-pipeline-probe.py`); record results and limitations.
- Manual checks: Assess deployed workflow with disposable data, live error and timeout paths, provider retention, model outcomes and latency, and residual risk.
- Success criteria: Explicit agreed risk decision or reviewed mitigation supported by appropriate evidence; no claim of perfect detection.
- Documentation impact: Update spec, guide or claims if approved behavior or risk claims change.
- Required next rerun: After relevant follow-up changes or substantive new evidence.
- Blocker or decision needed: Human risk acceptance, representative live/deployment evidence and decisions on any policy change.

## Findings and axis reports

The following assigned artifacts are reproduced in roster order. Their findings, statuses, evidence and limitations are retained; the two open High findings overlap but are not merged.


## Axis: Code quality

# Code Quality Review Report

## Status
- Target: scoped current worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`, including untracked reviewer tests.
- Scope: changed hint implementation, LLM client, settings, job deadline and startup; associated tests, configuration, spec and guide were considered as context. Unrelated changes excluded.
- Overall: PASS on this axis; no open code-quality findings.
- Independent human review: READY on this axis, subject to other axes and limitations.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Supplied evidence | Follow-up report records mypy passing; not independently rerun. |
| Tests | Supplied evidence | Follow-up report records 200 backend tests passed with mocked external services; not independently rerun. |
| Smoke/acceptance testing | Partial | Supplied synthetic live probe exercises the implemented pipeline and four reviewer cases; small sample and no deployed service. |
| Static analysis | Supplied evidence | Follow-up report records Ruff format and lint passing; not independently rerun. |
| Packaging/resources | Supplied evidence | Live pipeline report records successful `uv build` after obtaining build dependency; not independently rerun. |
| Specification validation | Outside axis | Contract review owns requirements assessment. |
| Documentation consistency | Outside axis | Contract review owns documentation assessment. |

## Next actions
- Implementation follow-up required: NO on this axis.
- Edit documentation: NO on this axis.
- Rerun code-review skill: AFTER FOLLOW-UP WORK if relevant changes occur.
- Reason: The prior diagnostic finding remains fixed; no further material maintainability defect was identified.

## Agent handoff
- Follow-up required: NO on this axis.
- Current implementation/review state: Prior quality finding fixed; other axes assess live classifier behavior and release readiness.
- Next responsible skill or human: Consolidating reviewer and independent human reviewer.
- Priority and finding addressed: `CQ-private-hint-reviewer-01`, fixed.
- Exact files and line locations: `backend/app/ai/hints.py:186`.
- Required change or investigation: None on this axis.
- Constraints and out-of-scope work: Preserve approved fail-open behavior, content-free diagnostics and cancellation semantics.
- Verification commands: Follow-up report records backend pytest, Ruff and mypy; live report records `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build`.
- Manual checks: Assess real deployment and residual classifier risk; the supplied live probe is limited.
- Success criteria: No open code-quality finding; other review axes assessed separately.
- Documentation impact: None on this axis.
- Required next rerun: After relevant changes.
- Blocker or decision needed: None on this axis.

## Findings
- `CQ-private-hint-reviewer-01` — [Medium] Unexpected reviewer bugs are indistinguishable from expected fail-open failures — Status: Fixed
- Category: Error handling and operator diagnostics.
- Location: `backend/app/ai/hints.py:186`.
- Requirement: Distinguish unexpected implementation failures from expected reviewer failures without logging protected content, preserving fail-open behavior and cancellation.
- Evidence: Expected errors produce a content-free warning; other `Exception` instances produce a distinct content-free error. Cancellation is not caught. The follow-up report records diagnostic and cancellation test coverage.
- Expected / actual: Unexpected failures are distinguishable from expected failures while the guarded hint is returned.
- Reproduction or inspection path: Inspect `_review_hint` exception handlers and supplied follow-up report.
- Impact: Operators can distinguish unexpected failures without disclosing exception content.
- Likely cause / confidence: Previously shared broad handler; high confidence from source inspection.
- Fix direction and affected responsibility: Completed in reviewer error handling.
- Tests to add/update: None identified on this axis.
- Documentation impact: None.
- Verification after fixing: Source inspected; follow-up report records focused and full tests and static checks, not independently rerun here.

## Positive observations
- The private reviewer is separated from generator tool handling, has explicit input and time bounds, and validates verdict shape strictly.
- Job deadlines use the event-loop clock; cancellation propagates through reviewer error handling. Model selection remains explicit at the gateway boundary.

## Gaps and limitations
- This specialist review covers code quality, not security, contract compliance or test adequacy. No checks were independently executed.
- The supplied live probe observed a working-code candidate allowed by a valid verdict; four examples do not establish classifier accuracy or production latency. The probe does not establish deployed behavior or provider retention.

## Manual checks for user
- Assess the synthetic live results and residual fail-open and classifier risks, and exercise the deployment separately.

## Conclusion
- The prior quality finding is fixed; no new material code-quality findings were identified.


## Axis: Specification and contracts

# Specification and Contract Review

## Status
- Target: scoped current worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`.
- Scope: private hint reviewer implementation, tests, backend specification and Developer Guide; unrelated work excluded.
- Overall: BLOCKED: source-level contracts are mapped, but live classifier and deployment acceptance remain limited.
- Independent human review: BLOCKED pending assessment of live false negative and other review axes.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation, tests, static analysis | Not independently run | Outside this specialist axis; follow-up report records 200 mocked backend tests and static checks. |
| Packaging/resources | Reported passed | Supplied live evidence reports `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build` succeeded; not independently rerun. |
| Smoke/acceptance testing | Partial | Supplied synthetic live probe exercised catalog, generator tools and reviewer; no deployed or persisted production job. |
| Specification validation | Partial | AC-01–07 mapped below; classification reliability and real latency remain unproven. |
| Documentation consistency | Verified by inspection | Changed spec and guide compared with implementation and approved task. |

## Requirement mapping
- AC-01, AC-07 — Verified by source and test inspection: generator guards and three-round limit precede review; empty hints fail; tests distinguish generator and reviewer calls. Execution evidence in the supplied follow-up report is mocked.
- AC-02 — Verified by inspection: separate model settings and generator override; global model retained for other calls; reviewer not checked at startup. Live evidence reports both configured IDs present and generator tool calls functioning for one synthetic case.
- AC-03 — Verified by inspection: reviewer receives question context, guarded candidate and hidden expected outputs, without hidden input fields or tools; fresh nonce/canary and lossless encoded spotlighting are used. Synthetic hostile-tag case was withheld, but one case cannot establish injection resistance.
- AC-04 — Verified by inspection: exactly two actual boolean fields, no duplicates; negative verdict withholds. Live probe observed valid verdicts. A valid verdict is not proof of accurate classification: a complete working-code solution was allowed.
- AC-05 — Verified by inspection: reviewer errors, invalid verdicts, canary leaks and timeout fail open with content-free logs; generator guard remains mandatory. Live failure paths were not exercised by the supplied probe.
- AC-06 — Verified by inspection: 64 KiB payload bound, 20-second reviewer limit, one-second margin, skip on insufficient time, cancellation not caught. Four reviewer samples of 0.12–0.13 seconds do not establish tail latency or gateway size limits.
- Spec §§7.1 and 8 and Developer Guide: verified by inspection against changed configuration, startup, data flow and resource limits. Assignment deployment separation is unaffected; deployed behavior is not established.

## Next actions
- Implementation follow-up required: NO for a confirmed contract defect; human assessment of observed false negative remains necessary.
- Edit documentation: NO for a confirmed inconsistency.
- Rerun code-review skill: AFTER FOLLOW-UP WORK if behavior or documentation changes.
- Reason: Approved contract specifies the reviewer verdict handling and explicitly acknowledges misses; live evidence demonstrates a residual risk, not a violation of a specified accuracy threshold.

## Agent handoff
- Follow-up required: BLOCKED for full acceptance and risk assessment.
- Current implementation/review state: No open contract findings; previous two specification findings remain fixed by inspection.
- Next responsible skill or human: AI owner and independent human reviewer.
- Priority and finding addressed: Assess live false negative and approved fail-open residual disclosure risk.
- Exact files and line locations: `backend/app/ai/hints.py:21`, `backend/app/ai/hints.py:139`, `workflow/live-ai/hint-current-pipeline-2026-11-09.md`.
- Required change or investigation: Decide whether observed solution disclosure is acceptable and whether further representative synthetic evaluation or a revised requirement is needed.
- Constraints and out-of-scope work: Do not treat classifier as an enforcement guarantee or change approved fail-open policy without direction; preserve privacy and unrelated work.
- Verification commands: Supplied probe command is `.venv/bin/python ../workflow/live-ai/hint-current-pipeline-probe.py` from `backend/`; use synthetic data and record limitations.
- Manual checks: Assess deployed workflow, live error paths, reviewer accuracy, provider retention and production latency as applicable.
- Success criteria: Human explicitly assesses residual risk and outstanding evidence; other review axes resolved.
- Documentation impact: Update claims if behavior or acceptance decision changes; do not describe probabilistic classification as guaranteed.
- Required next rerun: After relevant follow-up changes or evidence.
- Blocker or decision needed: Human risk acceptance and representative live/deployment evidence.

## Findings
- `SC-private-hint-1` — [High] Reviewer can receive a different candidate from the hint returned — Status: Fixed
- Category: Acceptance contract / protected answer review.
- Location: `backend/app/ai/hints.py:144`.
- Requirement: Reviewer receives the guarded candidate faithfully.
- Evidence: JSON encoding escapes angle brackets before spotlighting; hostile-content test checks round-trip fidelity.
- Expected / actual: Tag-like candidate content is preserved rather than removed.
- Reproduction or inspection path: Inspect `_review_hint` and hostile-content test.
- Impact: Previously identified content mismatch corrected for the reviewed path.
- Likely cause / confidence: Encoding avoids destructive tag removal; high confidence by inspection.
- Fix direction and affected responsibility: Completed in reviewer payload construction.
- Tests to add/update: Hostile-content round-trip test exists.
- Documentation impact: Spec documents encoding.
- Verification after fixing: Source and test inspected; follow-up report records suite execution.

- `SC-private-hint-2` — [Medium] Developer Guide describes obsolete model configuration and hint data flow — Status: Fixed
- Category: Developer documentation.
- Location: `docs/DeveloperGuide.md:88`.
- Requirement: Developer instructions reflect model configuration and protected data flow.
- Evidence: Guide names generator and reviewer settings, startup checks, fail-open behavior, boundaries and limits.
- Expected / actual: Guide aligns with reviewed source and spec.
- Reproduction or inspection path: Compare guide with configuration, startup and hint implementation.
- Impact: Prior misleading setup and data-flow claims corrected.
- Likely cause / confidence: Documentation updated alongside implementation; high confidence by inspection.
- Fix direction and affected responsibility: Completed in Developer Guide.
- Tests to add/update: None required for documentation correction.
- Documentation impact: Correction complete.
- Verification after fixing: Compared documented claims with source.

## Positive observations
- The spec describes reviewer-only hidden outputs and the approved fail-open exception; the guide qualifies reviewer quality.
- Live evidence establishes model catalog availability and a synthetic tool-call path, superseding the earlier absence of all live evidence.

## Gaps and limitations
- One live full-solution candidate was allowed. Approved requirements contain no accuracy threshold, so this is a significant demonstrated residual risk requiring human assessment, not a newly asserted contractual defect.
- Small samples do not establish recall, injection resistance, provider retention or production tail latency; no deployed service or persisted production job was exercised. This reviewer did not run tests or the probe.

## Manual checks for user
- Review observed false negative and fail-open risk; evaluate representative synthetic cases and deployed behavior, including failure and timeout paths, as needed for release.

## Conclusion
- No open specification findings; full acceptance remains blocked by unresolved evidence and human risk assessment.


## Axis: Security boundaries

# Security Boundary Review

## Status
- Target: scoped current worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`; assigned backend hint changes, tests, backend spec and Developer Guide.
- Scope: hint generation and private reviewer, answer exposure, prompt boundary, provider data, logging, resource limits and related configuration. Unrelated worktree changes excluded.
- Overall: FINDINGS — an observed valid false negative demonstrates a security risk; the approved design explicitly permits probabilistic misses and fail-open behavior, so this is not asserted to violate the acceptance contract.
- Independent human review: NOT READY pending explicit assessment of the observed disclosure risk.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Not run | Outside this specialist axis. |
| Tests | Evidence inspected | Follow-up review reports 200 passing backend tests with mocked dependencies; not rerun here. |
| Smoke/acceptance testing | Partial | Supplied `workflow/live-ai/hint-current-pipeline-2026-11-09.md` and probe: synthetic live gateway cases, one trial each. No deployed service or production data tested. |
| Static analysis | Complete with limits | Root `sh workflow/security/semgrep.sh /tmp/codeit-hint-live-security-semgrep.json`, exit 0, Semgrep 1.170.0 OSS, 225 unpinned Registry rules, 112 files scanned, no reported errors, ~100% parsed lines. Two wildcard CORS matches in `backend/app/main.py:67` and `code-execution/app/main.py:62` are pre-existing configuration risks, not demonstrated new bypasses. Scan considers tracked files under application roots, not Python tests, specs, configuration, dependencies or deployment; detailed skipped list unavailable. |
| Packaging/resources | Not independently run | Supplied live evidence reports successful backend build; resource limits inspected in source. |
| Specification validation | Inspected | Task AC-01–07 and backend spec §§7.1, 8; explicitly approved fail-open and no classifier guarantee. |
| Documentation consistency | Inspected | Spec and guide disclose private reviewer and fail-open; no documentation defect established on this axis. |

## Next actions
- Implementation follow-up required: YES — investigate and reduce the observed solution-disclosure risk, subject to the approved behavior and product decision.
- Edit documentation: AFTER CODE FIX if behavior or risk claims change.
- Rerun code-review skill: AFTER FOLLOW-UP WORK.
- Reason: a valid live verdict allowed a complete working solution; the approved design does not guarantee detection, but the demonstrated consequence needs an explicit risk decision.

## Agent handoff
- Follow-up required: YES
- Current implementation/review state: Synthetic live reviewer probe produced a valid allow verdict for complete working code; the end-to-end generator was not shown to produce that candidate.
- Next responsible skill or human: AI implementation owner and independent human reviewer.
- Priority and finding addressed: High risk, `SB-private-hint-live-01`.
- Exact files and line locations: `backend/app/ai/hints.py:21`, `backend/app/ai/hints.py:113`, `backend/app/ai/hints.py:185`, `backend/app/ai/hints.py:192`; `workflow/live-ai/hint-current-pipeline-probe.py` solution_leak case.
- Required change or investigation: Assess whether the demonstrated leakage is acceptable; if not, improve the approved protection and validate with representative synthetic cases. Changes to approved fail-open policy require product direction.
- Constraints and out-of-scope work: Preserve private data, approved model/data boundaries and failure semantics unless changed by the user. Do not interpret one sample as a recall estimate.
- Verification commands: Run backend tests and an authorized synthetic live probe through the actual pipeline after changes; record verdicts and limitations without protected content.
- Manual checks: AI owner should evaluate representative benign, full-solution, hidden-output and adversarial synthetic cases and assess provider retention and production deployment behavior.
- Success criteria: Risk owner explicitly accepts the observed residual risk, or a reviewed mitigation has evidence commensurate with its claimed protection; no claim of perfect detection.
- Documentation impact: Update spec/guide if approved behavior or stated limitations change.
- Required next rerun: After relevant implementation, test or evidence changes.
- Blocker or decision needed: Human risk decision; production recall and provider retention remain unknown.

## Findings
- `SB-private-hint-live-01` — [High] Valid reviewer verdict allowed a complete working solution — Status: Open
- Category: Answer leakage / probabilistic security control risk.
- Location: `backend/app/ai/hints.py:21`, `backend/app/ai/hints.py:113`, `backend/app/ai/hints.py:185`, `backend/app/ai/hints.py:192`.
- Requirement: Task AC-04 accepts a valid positive verdict; spec §8 explicitly says the reviewer is an additional defense, not a guarantee. The reviewer prompt defines working solution code as revealing the answer.
- Evidence: The supplied live probe directly passed a synthetic complete sum-program solution to `_review_hint` with the real configured reviewer and recorded a valid allow verdict and normal return. The same small probe withheld a direct hidden-output disclosure and a tag-injection answer case and allowed a benign hint. `run_hint` returns the guarded candidate when review returns normally; the deterministic guard limits length and multi-line fenced code, not all working solutions.
- Expected / actual: The reviewer was instructed to flag working solution code, but allowed this candidate. This is an observed model false negative, not proof that strict verdict parsing or approved acceptance logic is broken.
- Reproduction or inspection path: Inspect `workflow/live-ai/hint-current-pipeline-probe.py` case `solution_leak` and its recorded outcome in `workflow/live-ai/hint-current-pipeline-2026-11-09.md`; compare `_review_hint` and `run_hint`.
- Impact: If the generator emits a similar candidate and the reviewer again allows it, a student receives a complete solution. The probe did not demonstrate generator emission or a production leak; one sample cannot quantify frequency. Approved timeout, invalid-response and size/time-budget fail-open paths also permit unreviewed guarded candidates.
- Likely cause / confidence: Probabilistic semantic classification missed the solution; high confidence in the recorded single synthetic observation, low confidence about real-world prevalence and underlying model reason.
- Fix direction and affected responsibility: AI owner and product owner should assess this consequence and improve or explicitly accept the control's residual risk. Any change to fail-open policy needs user approval.
- Tests to add/update: Add representative synthetic complete and near-complete solutions, benign hints, hidden-output leakage and adversarial input to live evaluation; keep deterministic mocked decision and failure tests. Evaluate repeated cases without presenting a small sample as an accuracy guarantee.
- Documentation impact: Update risk/behavior statements if mitigation or policy changes.
- Verification after fixing: Re-run backend tests and authorized synthetic live evaluations with actual configured model and pipeline; document misses, false positives and limits.

## Positive observations
- Source separates generator visible tests from reviewer-only hidden expected outputs; reviewer receives no hidden inputs or tools. Reviewer output is parsed privately and not returned.
- Strict JSON validation rejects duplicate and extra fields and non-booleans; encoding and nonce-delimited untrusted data preserve tag-shaped content. Reviewer errors log content-free messages. Time and input bounds and cancellation behavior are covered by supplied mocked evidence.
- Live synthetic probe established both configured model IDs were available and observed the reviewer withholding two disclosure examples; these observations do not establish reliability.

## Gaps and limitations
- The live working-code case directly exercises the reviewer, not a generated candidate completing a persisted job. The generator pipeline sample was rejected, but its candidate was not retained, so appropriateness cannot be assessed. Four cases, one trial each, do not estimate recall or tail latency.
- Semantic prompt-injection resistance, provider retention, live gateway failures, production deployment and actual private-data handling outside the application are not established. The provider receives hidden expected outputs by approved design.
- Authentication and ownership code was unchanged and role/owner/state enforcement was not independently exercised. Supplied prior follow-up review covers source inspection and mocked boundary tests; no broad authentication audit is claimed.
- Scan findings concern unchanged open CORS; origin exposure and executor deployment remain existing operational risks. Registry rule contents are unpinned and excluded paths are not covered.

## Manual checks for user
- AI/risk owner: decide whether the observed solution leak and approved fail-open paths are acceptable for the intended deployment, and assess synthetic adversarial and benign examples, provider retention and deployment configuration.

## Conclusion
A valid private-reviewer verdict allowed a synthetic full solution. This demonstrates a material residual security risk within the expressly probabilistic design, not a proven violation of its approved fail-open contract. Human risk assessment remains necessary.


## Axis: Verification and evidence

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

## Consolidated gaps and limitations

The specification axis remains blocked. Small synthetic samples do not establish recall, injection resistance, provider retention, production latency or deployed behavior. The generated candidate in the single pipeline case was not retained. The aggregator did not rerun checks or independently review source; executor attribution and further limitations are in the axis reports.

## Manual checks for user

AI and release owners should assess the observed false negative and approved fail-open risk, representative synthetic cases, deployed workflow and live failures, provider retention and production latency.

## Conclusion

FAIL: resolve or explicitly assess the High disclosure risk and blocked acceptance evidence before independent human review is ready.
