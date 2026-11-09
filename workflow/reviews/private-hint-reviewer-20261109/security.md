# Security Boundary Review

## Status
- Target: current scoped worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`.
- Scope: private hint reviewer and its affected AI, answer confidentiality, job deadline and gateway boundaries; unrelated changes excluded.
- Overall: BLOCKED — no code defect identified, but live model and gateway behavior remains unverified and the static scan has a parser limitation.
- Independent human review: BLOCKED pending assessment of the stated residual risks and live evidence.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation | Not independently run | Implementation evidence records successful mypy; build was blocked by missing setuptools. |
| Tests | Evidence reviewed | Implementation evidence records 194 passing backend tests with mocked external HTTP; not rerun in this review. |
| Smoke/acceptance testing | Partial | Mock tests exercise isolation, verdicts, failures, limits and cancellation; no live gateway or adversarial classifier verification. |
| Static analysis | Partial | `sh workflow/security/semgrep.sh /tmp/codeit-private-hint-semgrep.json`, exit 0, Semgrep 1.170.0 OSS, 225 current Registry rules, 112 tracked files scanned (44 Python, 68 TypeScript); approximately 99.9% parsed. `backend/app/clients/llm.py:124` partial parsing; manually inspected gateway error path. Tests, specs, configuration and untracked files excluded; four of 116 candidates not scanned. Two wildcard CORS matches in backend and executor are pre-existing and unchanged; no introduced finding identified. Registry contents are not pinned. |
| Packaging/resources | Not independently run | Out of security-axis scope; build limitation above. |
| Specification validation | Inspected | Task and updated backend spec explicitly approve reviewer-only hidden outputs, bounded fail-open and canary exception. |
| Documentation consistency | Inspected | Task and implementation evidence disclose fail-open and classifier limitations. Matrix rows DATA-01, AI-01 and AI-02 were reviewed as planning evidence. |

## Next actions
- Implementation follow-up required: NO
- Edit documentation: NO
- Rerun code-review skill: NO, unless follow-up changes are made.
- Reason: No confirmed introduced security defect; approved fail-open behavior and probabilistic classification retain material residual risk.

## Agent handoff
- Follow-up required: BLOCKED
- Current implementation/review state: Source and mocked evidence reviewed; live gateway availability, latency and adversarial performance are unverified.
- Next responsible skill or human: AI owner and independent human reviewer.
- Priority and finding addressed: Residual answer disclosure and injection risk; no finding assigned.
- Exact files and line locations: `backend/app/ai/hints.py` reviewer flow; `backend/app/clients/llm.py:124` scanner parsing limitation.
- Required change or investigation: Assess live model availability and latency and perform authorized synthetic benign/adversarial probes without production secrets; assess whether approved fail-open risk is acceptable.
- Constraints and out-of-scope work: Preserve approved fail-open policy; use synthetic data; do not expose hidden outputs or reviewer output in logs or responses.
- Verification commands: Repeat the documented Semgrep command with a compatible parser when available; conduct project-authorized live AI probes.
- Manual checks: Verify gateway model availability, latency and classifier behavior using synthetic cases.
- Success criteria: Evidence covers relevant live boundaries and the human reviewer accepts remaining leakage risk.
- Documentation impact: Update evidence if further verification is performed.
- Required next rerun: After relevant changes or new verification evidence.
- Blocker or decision needed: Live credentials and live service evidence were not available in the supplied evidence; scanner partially parsed the gateway file.

## Findings
No confirmed findings.

## Positive observations
- Generator tools exclude hidden cases; reviewer receives hidden expected outputs, not hidden inputs, in separately spotlighted data. Reviewer has no configured tools and its output is never forwarded.
- Verdict parsing rejects duplicate keys, extra keys and non-boolean values. Invalid responses, canary leaks and call errors return the guarded candidate with content-free warnings, as expressly approved; cancellation is not caught by `except Exception`.
- Time and input limits bound reviewer work; the deadline leaves a one-second margin. Generator guards remain before review.

## Gaps and limitations
- The reviewer and gateway become additional readers of hidden expected outputs. Spotlighting and a canary are probabilistic protections, not an isolation guarantee. Valid malicious or mistaken verdicts can approve a leaking hint; invalid verdicts, timeouts, oversized inputs and insufficient time deliberately fail open. Existing evidence observed 7/9 bad examples caught, not proof of broad recall or injection resistance.
- Source inspection and mocked requests cannot establish provider retention, live model availability, production latency, or real adversarial classifier performance. No live request was made in this review.
- Authentication and ownership code was not changed; this review did not independently exercise all role and ownership cases. Scanner exclusions and partial parsing prevent a complete static security assessment.

## Manual checks for user
- AI owner: use synthetic protected outputs and hostile and benign examples to verify live gateway behavior and assess latency and classifier outcomes before relying on this control.

## Conclusion
No confirmed introduced security finding. Review completion is limited by unavailable live evidence and partial scanner coverage; the approved fail-open policy leaves a known answer-disclosure risk.
