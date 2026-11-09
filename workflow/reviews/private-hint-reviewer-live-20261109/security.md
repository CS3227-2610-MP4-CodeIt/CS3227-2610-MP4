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
