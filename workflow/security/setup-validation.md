# MP4 setup and validation evidence

Date: 5 November 2026 (SGT). Target: `190e98d8579dedb30d72408d94d9f2a1a6cf31e1`
plus the uncommitted setup files. Initial MP4 worktree was clean. MP4 source,
component manifests/lockfiles, specs, tests and existing workflow conventions were
inspected first. MP3 was a read-only reference for the profile structure, scan
script/policy and CI patterns. No MP3 application code, test results or product
security assertions were imported. `/implement` was not used.

## Delivered setup

1. [.codex/config.toml](../../.codex/config.toml) registers `task_implementer`,
   `code_quality_reviewer`, `spec_contract_reviewer`, `security_boundary_reviewer`,
   `verification_reviewer`, and `review_aggregator`. Each profile routes to the
   existing skill or aggregator contract, stays within its role, and forbids
   delegation. Model, reasoning and permissions inherit session settings.
   Existing `.codex/hooks.json` is unchanged; MP3's old notification setting was
   not copied. Registrations and standalone profile fields follow the
   [official config reference](https://learn.chatgpt.com/docs/config-file/config-reference)
   and [custom agent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents).
2. [Semgrep](semgrep.md) shares one advisory command between local use and CI,
   covering the backend, executor and frontend source. The review check reference
   now links this setup instead of saying it is absent.
3. The [MP4 matrix](security-matrix.md) applies the OWASP threat-modeling skill's
   assets/actors, flow, threat, control-owner and acceptance-case structure. It
   separates source inspection, observed tests and planned probes, including
   hidden-test confidentiality, model read tools, hostile submitted Python,
   deployment gaps and development-agent authority/evidence attacks.
4. Four application/security workflows supplement the existing Pages workflow:
   [backend](../../.github/workflows/backend.yml),
   [executor](../../.github/workflows/code-execution.yml),
   [frontend](../../.github/workflows/frontend.yml),
   [Semgrep](../../.github/workflows/security.yml).
   Each supports manual dispatch and relevant PR/push path filters. Application
   checks run on pushes to any branch; security pushes target master. All use
   `contents: read`, SHA-pinned actions, no persisted checkout credentials and
   ten-minute job limits. Python 3.14 uses `uv sync --locked`; Node 24 (matching
   the frontend Dockerfile) uses `npm ci`. The executor suite runs on Ubuntu.
   No deployment steps, application secrets or branch-protection rules added.

## Observed checks

Python commands ran in the relevant service directory using existing environments.
Initial `uv` commands were blocked by the sandbox's access to `~/.cache/uv`;
check commands then succeeded with `UV_CACHE_DIR=/tmp/codeit-uv-cache` and
`--no-sync`, without installing dependencies or changing lockfiles.

| Area | Command / directory | Actual outcome |
| --- | --- | --- |
| Backend format | `uv run --locked --no-sync ruff format --check .`, `backend/` | Passed, 47 files already formatted. |
| Backend lint | `uv run --locked --no-sync ruff check .` | Passed. |
| Backend types | `uv run --locked --no-sync mypy app` | Passed, 33 source files. |
| Backend tests | `uv run --locked --no-sync pytest -q` | Passed, **134 tests**, 14.80 s. Temporary DB and mocked SoCLaaS/executor; no live integration claim. |
| Executor format/lint/types | Same first three Python commands, `code-execution/` | Passed; 16 formatted files, 10 mypy source files. mypy targets Linux by configuration. |
| Executor runtime tests | Linux suite configured in CI; local Docker availability checked | **Blocked locally**: host is macOS and Docker daemon is not running. Did not execute hostile-program tests on an unsupported host. |
| Python packages | `uv build --offline`, both Python projects | **Blocked**: `setuptools>=75` missing from uv cache. Confirmed in both temporary and existing caches; approved cache access did not resolve it. CI uses online `uv build`; package success is unverified. |
| Frontend format | `npm run format:check`, `frontend/` | Passed. |
| Frontend lint | `npm run lint` | Exit 0 with two existing `only-export-components` warnings in AuthProvider/EventsProvider. |
| Frontend tests | `npm test` | Passed, **41 tests across 9 files**. Node warned that localStorage was unavailable without a storage file. |
| Frontend compilation/build | `npm run build` | Passed (TypeScript and Vite); warning about a roughly 1,009 kB minified JS chunk (318 kB gzip). Local Node 26.8.2; CI/container targets Node 24, not locally exercised. |
| Static security | Shared script, repository root | Exit 0, 225 rules, 106 source files, two pre-existing CORS findings and one partial parser warning. See [exact coverage/triage](semgrep.md). |
| Agent TOML | Python 3.14 `tomllib` on config and six profiles | Parsed; all registered paths exist, names match, instruction targets resolve, no model/sandbox overrides. Profile selection in a fresh live session was not exercised; this does not prove runtime discovery. |
| Workflow YAML | Ruby/Psych parse of all five workflows, plus structural assertions on four new workflows | Passed syntax, triggers, read-only permissions, runner/timeout, action SHA, checkout credential and service-directory checks. `actionlint` unavailable; no GitHub execution claim. |
| Shared shell | `sh -n`; invalid args/output and missing scanner checks; stubbed scanner from `/tmp` | Passed expected exit/argument/root/flags/error propagation behavior. Stubbed tests do not replace the actual scan. |
| Integrity/docs | Local links and matrix test names checked; `git diff --check` | Passed. Application source, lockfiles, Pages workflow and telemetry hook unchanged. |

## Remaining validation and follow-up

- Run the new workflows on GitHub to validate hosted-runner dependency installation,
  action pins, Python packaging, Node 24 and the Linux executor suite. No workflow
  was dispatched and no commit was created, so Actions execution remains unobserved.
- Exercise named profile selection in a fresh trusted project session before relying
  on delegation. Static parsing does not prove role discipline; DEV-01–04 remain
  planned paired benign/adversarial evals.
- WEB-01/EXEC-01 retain the confirmed wildcard-CORS risks; choose production origin
  and network policy through a separate product/security change. EXEC-02/OPS-01
  retain high-priority hostile-code isolation and deployment-validation gaps.
- Complete matrix acceptance cases for denied mutation state preservation,
  mid-job membership changes, unknown model tools, semantic answer leakage,
  cross-job isolation, browser integration, live model behavior and deployment.
  These are explicit unproven boundaries, not requirements implemented by this setup.

Setup review found no remaining setup defect in the assessed local scope. It is
ready for human review with the above blocked checks. This is not a production
security or release pass. No commits, pushes, deployments, branch protection,
application behavior changes, model eval runs or live AI calls were performed.
