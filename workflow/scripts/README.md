# Admin summary verification runners

Task 1 was accepted **PASS WITH LIMITATIONS (WARN)** on 7 November 2026 (Asia/Singapore). The recorded contract experiment improved from 7/18 to 18/18 passing; supplemental tests passed 16/16 and the final full backend suite passed 168/168. See the [accepted task](../tasks/admin-summary-response-reliability.md) and [security closeout](../reviews/admin-summary-task1-security-closeout.md) for provenance, independent agent roles and limitations. This is not production-security approval.

## Prerequisites and commands

Use PowerShell with Git and a working Docker Desktop Linux-container engine. Run from the repository root. The scripts build allowlisted temporary snapshots of current working source, including the Admin change, and create uniquely named disposable containers/images. No Windows Python/Semgrep installation, application server, host mount, environment file or database volume is required. Do not supply credentials.

```powershell
# Original 18-case contract suite and 16 supplemental cases:
.\workflow\scripts\run-admin-summary-baseline.ps1 -Suite Baseline
.\workflow\scripts\run-admin-summary-baseline.ps1 -Suite Supplemental

# All backend tests, including Admin, guards, jobs, Teacher and Student:
.\workflow\scripts\run-admin-summary-baseline.ps1 -Suite Full

# Ruff format/lint, mypy and offline package build, with build-cache setup:
.\workflow\scripts\run-admin-summary-baseline.ps1 -Suite Quality -PrepareBuildCache

# Validate Semgrep's source snapshot without Docker, then run a fresh scan:
.\workflow\scripts\run-admin-summary-semgrep.ps1 -SnapshotOnly
.\workflow\scripts\run-admin-summary-semgrep.ps1
```

Run sequentially and inspect each run's result before proceeding. `-Suite Regressions` selects the five existing Admin/guard/job/Teacher/Student modules instead of the full suite. `-PrepareBuildCache` is valid only for Quality; it performs an online setup-stage build before the final offline check. Plain `-Suite Quality` does not prepare that cache and can stop at an uncached build dependency. Dependency-setup failure is not proof of a package defect; inspect the separate setup/offline logs and exit codes.

**Baseline means the original test set, not historical application source.** On accepted current code it should pass 18/18. Reproducing the historical 7/18 result requires a separate disposable snapshot of application source at `818fd61111677f1e8221776226ef09aa54e1b8b4` with the same 18 contract fixtures/expectations. Neither runner restores that source or switches branches. Do not change expectations to recreate the result.

## Network and local evidence

Image setup downloads public images/dependencies. Backend environments use Python 3.14.4 and locked runtime/development dependencies; the separately declared build backend may need downloading. Test/Quality containers use `--network none`; external services are mocked and SQLite data is temporary. No application-model or repair call is required.

The Semgrep image pins CLI 1.170.0 and invokes the existing `workflow/security/semgrep.sh` OSS policy. Metrics, autofixes and version checks are disabled. Its container needs network access for Registry packs; bridge networking is not a domain-restricted firewall. No login, token or source-upload command is supplied. Stop and review rather than adding credentials or weakening TLS if Registry access fails. Registry rules can change independently of the CLI pin; retained IDs do not establish immutable rule contents.

Each invocation writes a new `workflow/planning/admin-summary-<id>/` or `admin-semgrep-<id>/` directory. Read structured JSON/CSV and individual logs; Quality's generic text summary has pytest-oriented fields. The historical Quality run's PowerShell reporting exception did not invalidate its recovered all-zero check results. Raw directories referenced by review reports are local provenance and may be absent in a fresh checkout; the committed closeout preserves sanitized outcomes.

Keep raw findings, source snippets, pytest tracebacks, manifests, container logs, distributions and recovered copies local. They may contain synthetic session tokens, diagnostic context or machine paths; they are verbose generated output, not a public evidence summary. Do not blanket-stage `workflow/planning/`. The runners extract evidence before removing only their own disposable container/image and checked temporary context. If extraction fails, retain the named resources for recovery; do not prune or touch existing services/volumes. Base images and build cache remain.

## Security coverage and interpretation

Semgrep targets `backend/app`, `code-execution/app` and `frontend/src`, not the entire repository. The accepted scan reported 106 files scanned (33/10/63 respectively), two pre-existing wildcard-CORS findings, three prompt Markdown files and one CSS file unreported as scanned, and partial parsing in unchanged `backend/app/clients/llm.py` near line 122. Manual inspection and executed parser/job tests compensate within Task 1; they do not replace full static coverage.

Exit 0 is not proof of zero findings or security acceptance. Review `coverage.json`, `rules-used.json`, errors, skipped/unreported paths and `triage.csv`. Findings require human triage; neither suppressions nor application fixes are automatic. The baseline CORS risks remain separate follow-up work for production origins and private executor reachability. Live-provider behavior, factual prose, deployment isolation and Task 2 statistical interpretation remain outside this acceptance.
