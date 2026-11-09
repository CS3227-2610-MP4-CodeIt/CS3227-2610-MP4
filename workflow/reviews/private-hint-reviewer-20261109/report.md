# Code Review Report

## Status
- Target: current scoped worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`.
- Scope: `backend/.env.example`, `backend/app/ai/hints.py`, `backend/app/clients/llm.py`, `backend/app/config.py`, `backend/app/jobs/runner.py`, `backend/app/main.py`, `backend/tests/conftest.py`, `backend/tests/test_student.py`, `backend/tests/test_hint_reviewer.py`, and `specs/backend-spec.md`.
- Overall: FAIL — one High finding and an unresolved blocked security axis.
- Independent human review: NOT READY; security review also remains blocked on live evidence and scan coverage.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation/type checking | Passed by verification reviewer | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync mypy app`; 34 files, exit 0. |
| Tests | Passed with coverage gaps | Verification reviewer: `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync pytest -q`; 194 passed, mocked gateway/executor. See VR findings. |
| Smoke/acceptance testing | Partial / blocked | Mocked API workflow exercised; live gateway, browser, container and deployed workflow unverified. |
| Static analysis | Partial | Verification reviewer reports Ruff and diff checks passed; security reviewer reports Semgrep exit 0 with partial parsing and exclusions. Exact commands and limitations are retained below. |
| Packaging/resources | Blocked | Verification reviewer: `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build --offline` failed, missing cached setuptools. |
| Specification validation | Incomplete | Contract reviewer identified SC-private-hint-1; live behavior remains unverified. |
| Documentation consistency | Inaccurate | Contract reviewer identified SC-private-hint-2. |

## Next actions
- Implementation follow-up required: YES.
- Edit documentation: AFTER CODE FIX.
- Rerun code-review skill: AFTER FOLLOW-UP WORK.
- Reason: Correct candidate fidelity, safe diagnostics and acceptance coverage; update the Developer Guide and resolve or explicitly assess remaining evidence limitations.

## Agent handoff
- Follow-up required: YES; live security verification remains BLOCKED.
- Current implementation/review state: Five open findings across three axes; security axis blocked without a confirmed finding. Child assessments and evidence are retained in full below.
- Next responsible skill or human: implement-task owner; AI owner for authorized synthetic live checks; independent human reviewer after follow-up.
- Priority and finding addressed: High SC-private-hint-1; Medium CQ-private-hint-reviewer-01, SC-private-hint-2, VR-private-hint-01 and VR-private-hint-02.
- Exact files and line locations: `backend/app/ai/hints.py:147` and `:168`; `backend/app/ai/guards.py:64`; `docs/DeveloperGuide.md:88`, `:141`, `:154`; `backend/tests/test_student.py:742`; `backend/tests/test_hint_reviewer.py:57`; `backend/app/jobs/runner.py:56`; scanner limitation at `backend/app/clients/llm.py:124`.
- Required change or investigation: Preserve candidate content losslessly; distinguish unexpected failures using content-free diagnostics; add adversarial boundary and composed deadline tests; update guide; investigate live gateway behavior and scanner coverage.
- Constraints and out-of-scope work: Preserve approved fail-open policy, generator guards, cancellation, protected content, and unrelated changes. Use synthetic data for authorized live probes.
- Verification commands: Focused reviewer and student tests and full backend suite, Ruff and mypy; retry offline build with cached requirements and Semgrep with compatible parser. Exact child commands are below.
- Manual checks: Authorized synthetic gateway model availability, tool support, latency, classifier behavior, data boundaries and deployment smoke remain unverified.
- Success criteria: Address each open finding, pass relevant checks, supply or explicitly assess live and scanning evidence, and obtain human acceptance of residual fail-open risk.
- Documentation impact: Update Developer Guide after code fix and record further verification evidence.
- Required next rerun: Code review after follow-up changes or relevant new evidence.
- Blocker or decision needed: Live service credentials and authorization, cached build dependency, compatible scanner parsing, and human assessment of residual risk.

## Findings
Five open findings: one High and four Medium. Each complete finding, with its original ID, evidence, status and follow-up, is preserved under its assigned axis below.

## Positive observations
The children report strict verdict parsing, separation of the tool-free reviewer call, deadline handling, and tests for several failure paths. See axis sections for scope and qualifications.

## Gaps and limitations
Live gateway and classifier behavior, provider retention, production latency, browser, container and deployed behavior remain unverified. The security scan partially parsed the gateway file and excluded files; the offline package build lacked setuptools. The classifier experiment was small and reported two misses among nine bad examples. The aggregator did not rerun checks or independently review source; child-reported implementation evidence is not a reviewer rerun. Independence and isolation beyond the assigned specialist roles are not established in the artifacts.

## Manual checks for user
With appropriate authorization and synthetic data, verify model availability, generator tool support, reviewer behavior and latency, and deployment behavior; assess residual disclosure risk. See the axis handoffs for details.

## Conclusion
FAIL: resolve the High finding and blocked security axis, address remaining findings, and rerun review before independent human review.

## Axis: Code quality

# Code Review Report

## Status
- Target: current worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40`.
- Scope: code-quality axis for the assigned backend configuration, LLM client, hint reviewer, job runner, startup and tests; related spec and supplied task/evidence inspected for context.
- Overall: FINDINGS
- Independent human review: READY, subject to the limitations below.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Implementation and async boundaries | Complete | Inspected scoped diff and affected hint, client, startup and runner paths. |
| Static analysis | Complete | `cd backend && UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --no-sync ruff check .` and `uv run --no-sync mypy app` passed; `git diff --check` passed. |
| Compilation | Not independently run | Implementer reports mypy success. |
| Tests | Not independently run | Implementation evidence reports 194 backend tests passed, followed by one focused test after a test-only change. |
| Smoke/acceptance testing | Not independently run | Mocked tests and limitations are described in implementation evidence. |
| Packaging/resources | Unverified | Implementation evidence reports offline build blocked by missing setuptools. |
| Specification validation | Context inspected | Full contract review belongs to the assigned specialist. |
| Documentation consistency | Context inspected | Full documentation review belongs to the assigned specialist. |

## Next actions
- Implementation follow-up required: YES
- Edit documentation: NO
- Rerun code-review skill: AFTER FOLLOW-UP WORK
- Reason: distinguish expected fail-open reviewer failures from unexpected implementation defects while preserving content-free logging.

## Agent handoff
- Follow-up required: YES
- Current implementation/review state: reviewer failure handling masks unexpected defects as normal fail-open outcomes.
- Next responsible skill or human: implement-task.
- Priority and finding addressed: Medium, CQ-private-hint-reviewer-01.
- Exact files and line locations: `backend/app/ai/hints.py:168`–`186`.
- Required change or investigation: narrow expected exceptions or explicitly distinguish unexpected errors with a safe, content-free diagnostic; preserve approved fail-open behavior for reviewer failures.
- Constraints and out-of-scope work: never log protected inputs, provider output or exception text; preserve cancellation and approved reviewer failure behavior.
- Verification commands: `cd backend && UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --no-sync pytest -q tests/test_hint_reviewer.py tests/test_student.py` and relevant Ruff/mypy checks.
- Manual checks: Live gateway availability, real reviewer reliability and production latency remain unverified; mocked checks cannot establish these.
- Success criteria: expected failures and unexpected implementation failures remain content-free and distinguishable; cancellation and fail-open tests pass.
- Documentation impact: none anticipated.
- Required next rerun: code-quality review after follow-up.
- Blocker or decision needed: none.

## Findings
- `CQ-private-hint-reviewer-01` — [Medium] Unexpected reviewer bugs are indistinguishable from expected fail-open failures — Status: Open
- Category: Error handling and operator diagnostics.
- Location: `backend/app/ai/hints.py:168`–`186`.
- Requirement: Project standards call for deliberate failure handling and protected diagnostics; approved task requires call, timeout and invalid-verdict failures to fail open with content-free logging.
- Evidence: One `except Exception` encloses the gateway call, response field access, canary check and JSON/schema parsing and logs the same warning for all exceptions. An `AttributeError` or other programming defect in these operations therefore follows the same path as a gateway failure or malformed verdict.
- Expected / actual: Expected operational failures should remain safely fail-open while unexpected implementation failures are distinguishable without logging sensitive exception content. Currently both silently return the candidate with identical warnings.
- Reproduction or inspection path: Have the reviewer call or returned reply raise an unexpected `AttributeError`; `_review_hint` returns normally and logs the generic reviewer warning, just as for a malformed verdict.
- Impact: A regression can disable the reviewer across requests while appearing to be ordinary transient reviewer failure, delaying diagnosis of an unreviewed-hint path.
- Likely cause / confidence: Broad catch combines the external I/O and internal parsing boundaries; high confidence from inspection.
- Fix direction and affected responsibility: Classify expected gateway, timeout and verdict errors separately from unexpected internal errors; keep all diagnostic messages content-free and preserve approved fail-open behavior and cancellation semantics.
- Tests to add/update: Simulate an unexpected internal error and an expected reviewer error; verify distinct safe diagnostics and unchanged returned-hint behavior, with no protected content in logs.
- Documentation impact: none anticipated.
- Verification after fixing: focused reviewer and student tests, Ruff and mypy; inspect logs for absence of exception text and protected content.

## Positive observations
- Reviewer receives a separate tool-free call with fresh spotlighting and canary; strict verdict parsing rejects duplicate keys and non-boolean fields.
- Job deadlines use the event-loop clock and reviewer cancellation is not swallowed by the `Exception` handler.

## Gaps and limitations
- This specialist reviewed code quality only; security, specification and verification decisions belong to their respective reviewers.
- Live model availability, reviewer quality, gateway limits and latency remain unverified, as recorded in implementation evidence. Package build remains unverified.

## Manual checks for user
- Check configured generator and reviewer availability and representative reviewer behavior against the actual gateway when credentials are available; assess deployment latency separately.

## Conclusion
- One medium code-quality finding requires follow-up; no Blocker or High finding was identified on this axis.

## Axis: Specification and contracts

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

## Axis: Security boundaries

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

## Axis: Verification and evidence

# Code Review Report

## Status
- Target: current worktree against `e9c2f8f057716eaf04a80446941b2d96a42e5b40` (HEAD confirmed); scoped files listed in implementation evidence.
- Scope: verification of private hint reviewer, model configuration, job deadlines and associated tests; unrelated worktree changes excluded.
- Overall: FINDINGS
- Independent human review: READY with the limitations and follow-up below.

## Checks
| Area | Status | Command/evidence |
| --- | --- | --- |
| Compilation / type checking | Passed | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync mypy app`, 34 files, exit 0. |
| Tests | Passed | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync pytest -q`, 194 passed in 32.51s, exit 0. In-process, mocked gateway/executor. Coverage gaps below. |
| Smoke/acceptance testing | Blocked | Automated mocked API workflow exercised; live gateway, browser, container and deployed workflow not exercised. Metered live calls require explicit authorization. |
| Static analysis | Passed with limitation | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync ruff format --check .` and `ruff check .`, exit 0. `git diff --check` at root exit 0. Semgrep belongs to security review; no matching completed scan evidence supplied. |
| Packaging/resources | Blocked | `backend/`: `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build --offline`, exit 2: required setuptools unavailable in cache. No dependency installation attempted. |
| Specification validation | Passed with limitations | Compared task ACs and backend spec to implementation and tests; acceptance classification below. |
| Documentation consistency | Not applicable | Specialist did not review documentation consistency; assigned to contract review. |

## Acceptance evidence
- AC-01: Supported for existing generator guards and loop by existing tests and empty/canary/strip tests; the gateway is mocked.
- AC-02: Supported for default generator and reviewer request IDs and startup without reviewer in mock model list. Custom overrides and other feature selection are supported by source inspection, not independently exercised end to end.
- AC-03: Unsupported in part: benign markers verify reviewer output placement and tool omission, but hostile delimiter/instruction handling and full request/response secrecy matrix are not exercised (VR-private-hint-01).
- AC-04: Supported by strict parsing and four verdict-combination unit tests; negative verdict is also tested through a job.
- AC-05: Supported at unit level for exception, invalid verdict, canary and timeout and at job level for invalid verdict. Actual network/provider failures are mocked; no live behavior claimed.
- AC-06: Unsupported in part: size, insufficient time, cancellation and ordinary job timeout are individually tested, but the reviewer deadline and runner do not have a combined state-transition test (VR-private-hint-02). Live model availability, gateway input limits and latency are blocked/unverified. Reviewer availability does not block mocked startup.
- AC-07: Supported by bounded loop integration test: four generator requests and one reviewer request.

## Next actions
- Implementation follow-up required: YES (verification tests).
- Edit documentation: NO (within this review axis).
- Rerun code-review skill: AFTER FOLLOW-UP WORK.
- Reason: acceptance tests need to exercise security-boundary adversarial data and the composed reviewer/job deadline.

## Agent handoff
- Follow-up required: YES
- Current implementation/review state: backend checks pass with mocked dependencies; offline build blocked; two coverage findings remain.
- Next responsible skill or human: implement-task owner.
- Priority and findings addressed: Medium, VR-private-hint-01 and VR-private-hint-02.
- Exact files and line locations: `backend/tests/test_student.py:742`, `backend/tests/test_hint_reviewer.py:57`, `backend/app/jobs/runner.py:56`, `backend/app/ai/hints.py:137`.
- Required change or investigation: add outcome-focused integration coverage for hostile data and the reviewer deadline inside a real job; verify protected data stays private and job state reflects the specified outcome.
- Constraints and out-of-scope work: preserve approved fail-open behavior and generator/reviewer separation; no live calls without authorization.
- Verification commands: from `backend/`, `UV_CACHE_DIR=/tmp/codeit-uv-cache uv run --locked --no-sync pytest -q`, plus configured Ruff and mypy checks; retry offline build when build requirements are cached.
- Manual checks: authorized gateway model availability, bounded latency/input behavior, and deployment smoke remain unverified; use disposable data, never real hidden answers.
- Success criteria: added tests demonstrate expected protected boundaries and final persisted job outcomes, suite passes; explicitly record residual live and build limitations.
- Documentation impact: none identified on this axis.
- Required next rerun: verification review after test changes.
- Blocker or decision needed: cached build dependency and explicit authorization for metered live calls.

## Findings
- `VR-private-hint-01` — [Medium] Hostile reviewer input and private-output boundaries lack the approved integration coverage — Status: Open
- Category: acceptance / security-boundary verification.
- Location: `backend/tests/test_student.py:742`.
- Requirement: AC-03 requires hostile delimiter and instruction content with benign control, fresh spotlighting, and marker inspection across requests; DATA-01 requires reviewer text and hidden data excluded from job/error/log outputs.
- Evidence: the integration test uses ordinary marker strings, checks one generator request for hidden output, one reviewer request for hidden input and output, and failed-job error for one marker. It does not exercise hostile delimiters or instructions, freshness, all generator calls, nor secret reviewer response text across job result/error/log.
- Expected / actual: adversarial data remains within its wrapped data boundary and protected values never appear in public or logged output; current tests establish only a benign subset.
- Reproduction or inspection path: inspect `test_hint_private_reviewer_verdict_and_data_boundary` and `test_review_limits_and_failure_do_not_log_content`.
- Impact: regressions in reviewer data isolation or result/log redaction could pass the suite; mocked tests cannot establish semantic model resistance.
- Likely cause / confidence: planned matrix was only partially implemented; high confidence in the coverage gap.
- Fix direction and affected responsibility: backend test owner should exercise hostile candidate, context and tag-like hidden output plus benign control with distinct markers, inspect every generated request and persisted API result/error/log, and assert fresh wrapping/canaries without copying implementation logic.
- Tests to add/update: integration cases for hostile delimiters and private verdict/hidden-output markers; include generator tool rounds.
- Documentation impact: none.
- Verification after fixing: run focused tests and backend suite; live adversarial behavior remains separate evidence.

- `VR-private-hint-02` — [Medium] Reviewer deadline is not verified through the persisted job lifecycle — Status: Open
- Category: timeout / state-transition verification.
- Location: `backend/tests/test_hint_reviewer.py:57`; `backend/app/jobs/runner.py:56`.
- Requirement: AC-06 requires reviewer timeout before the enclosing job timeout, fail-open on insufficient time, and effective overall deadline and cancellation.
- Evidence: reviewer unit tests call `_review_hint` directly with no deadline or an already expired deadline; cancellation is injected directly. Existing job timeout/shutdown tests use independent handlers. No test combines delayed generator/reviewer calls with runner's computed deadline and persisted outcome.
- Expected / actual: a slow reviewer stops before the job deadline and persists the guarded hint; an actual overall timeout or shutdown still fails the job. These composed behaviors are not exercised.
- Reproduction or inspection path: compare reviewer limit tests with `backend/tests/test_jobs.py` timeout/shutdown tests.
- Impact: regressions in deadline propagation or cancellation handling can fail jobs or persist wrong outcomes while current isolated tests pass.
- Likely cause / confidence: unit-level limits and generic job tests do not cover their integration; high confidence in coverage gap.
- Fix direction and affected responsibility: backend test owner should add deterministic controlled-delay job tests using short budgets and assert persisted status/result and content-free logging, plus cancellation or shutdown while reviewer is active.
- Tests to add/update: reviewer-timeout fail-open within overall deadline, exhausted budget skip, and enclosing cancellation or timeout.
- Documentation impact: none.
- Verification after fixing: focused job/reviewer tests and full backend suite.

## Positive observations
- Tests cover all four verdict combinations, duplicate keys and other invalid schemas, stripped candidate, no review after empty/canary generator output, and a bounded tool loop.
- Reviewer unit tests cover oversize, failure logging, timeout and propagation of cancellation; startup mock excludes the reviewer model.

## Gaps and limitations
- No live model availability, classifier recall, production latency, gateway limits, container, browser, or deployed behavior established. The supplied classifier experiment has only 9 bad and 7 good examples and reports two bad misses.
- No applicable matching Semgrep result was supplied; security reviewer owns scan and triage.
- A discovery command using an unmatched `test_llm*` glob exited 1; subsequent targeted inspection used `rg` over the test directory. It was not a test failure.

## Manual checks for user
- When explicitly authorized, use a disposable environment to verify the configured models exist and a real hint/reviewer workflow respects the documented deadline and data boundary. Assess deployment separately; mocked checks do not prove it.

## Conclusion
- Automated backend checks passed, but the two acceptance coverage gaps and offline packaging limitation prevent a verification PASS.
