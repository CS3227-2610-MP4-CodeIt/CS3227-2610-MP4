# Security Boundary Review

## Status
- Target: scoped worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`, following corrections.
- Scope: private hint reviewer, hidden answers, prompt boundary, gateway and deadline; unrelated work excluded.
- Overall: BLOCKED — no confirmed introduced security defect; live gateway and classifier behavior remain unverified.
- Independent human review: BLOCKED pending assessment of live behavior and residual disclosure risk.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Not independently run | Outside this axis; previous implementation evidence reports mypy passed. |
| Tests | Evidence inspected | Current tests cover lossless hostile tag content and job timeout/shutdown paths; not independently executed in this review. Previous report's 194 passing tests predate follow-up corrections. |
| Smoke/acceptance testing | Partial | Mocked request and job tests inspected; no live gateway or adversarial model test performed. |
| Static analysis | Partial | Supplied `/tmp/codeit-private-hint-followup-semgrep-final.json`: Semgrep 1.170.0, 112 scanned paths, no reported errors, two pre-existing wildcard CORS findings in backend and executor. Supplied evidence reports exit 0. Shared script uses OSS `p/python` and `p/typescript` Registry packs; exact downloaded rule snapshot/count and skipped candidate list were not supplied. Scanned paths include changed backend application files; tests, specs, configuration and other excluded paths are outside the scan. A local `semgrep --version` attempt failed due to empty system trust anchors; no new scan was claimed. Findings concern unchanged open CORS configuration and do not establish a new bypass. |
| Packaging/resources | Not assessed | Outside security axis; prior offline build was blocked by unavailable setuptools. |
| Specification validation | Inspected | Task AC-01–07 and current backend spec authorize reviewer-only hidden outputs and bounded fail-open behavior. |
| Documentation consistency | Inspected | Task and prior evidence disclose classifier and fail-open limitations. |

## Next actions
- Implementation follow-up required: NO
- Edit documentation: NO
- Rerun code-review skill: NO, unless relevant changes follow.
- Reason: No confirmed introduced security defect; live classifier and provider behavior remain unproven.

## Agent handoff
- Follow-up required: BLOCKED
- Current implementation/review state: Source and supplied scan inspected; live model and gateway behavior unverified.
- Next responsible skill or human: AI owner and independent human reviewer.
- Priority and finding addressed: Residual disclosure and prompt-injection risk; no finding assigned.
- Exact files and line locations: `backend/app/ai/hints.py` reviewer flow and `backend/app/ai/guards.py` spotlighting.
- Required change or investigation: Assess gateway availability, latency, retention and classifier behavior using synthetic protected values and adversarial inputs; assess approved fail-open risk.
- Constraints and out-of-scope work: Preserve approved fail-open policy and do not disclose private content in logs or responses.
- Verification commands: Project-authorized live synthetic probes; rerun configured Semgrep scan if matching complete scan metadata is needed.
- Manual checks: Verify live model availability, timeout behavior and adversarial classification with synthetic data.
- Success criteria: Live evidence and explicit human assessment of residual disclosure risk.
- Documentation impact: Record any new evidence and limitations.
- Required next rerun: After relevant changes or new evidence.
- Blocker or decision needed: Live gateway and model behavior were not established by the supplied evidence.

## Findings
No confirmed findings.

## Positive observations
- Generator tools select visible test cases only; the private tool-free reviewer receives hidden expected outputs but not hidden inputs. Reviewer output is parsed privately and never forwarded.
- JSON encoding escapes angle brackets before spotlighting, preserving tag-like candidate, context and output text when decoded without allowing literal closing tags to escape the envelope. The revised hostile-content test checks candidate and hidden-output round trips.
- Strict verdict parsing rejects duplicate or extra fields and non-booleans. Reviewer failures and canary leaks log content-free messages and follow explicitly approved fail-open behavior; cancellation propagates.
- Reviewer size and deadline limits avoid silent truncation and bound the call. Current tests exercise timeout, exhausted budget and shutdown in the job lifecycle.

## Gaps and limitations
- Spotlighting and JSON encoding preserve the data boundary syntactically; they cannot guarantee semantic instruction resistance by a model. A mistaken or manipulated valid verdict, as well as any approved fail-open path, can allow a leaking candidate. Supplied prior classifier evidence observed 7/9 bad examples caught; it is not a broad recall estimate.
- Provider retention, real model availability, live latency, gateway limits and production behavior were not verified. The reviewer and gateway receive hidden expected outputs by approved design.
- Authentication and ownership code was unchanged and was not independently exercised across all roles and states. Static scan exclusions and missing rule snapshot limit its conclusions.

## Manual checks for user
- AI owner: perform authorized live synthetic benign and hostile probes, verify model availability and deadline behavior, and assess residual risk before relying on the classifier.

## Conclusion
No confirmed introduced security finding. Live security behavior and residual fail-open disclosure risk remain for human assessment.
