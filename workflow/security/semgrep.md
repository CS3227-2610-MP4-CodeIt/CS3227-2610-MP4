# CodeIt Semgrep setup and baseline

Run from the repository root (the script also resolves its root from other directories):

```sh
sh workflow/security/semgrep.sh
sh workflow/security/semgrep.sh /tmp/codeit-semgrep.json
```

JSON goes to stdout unless a local output file is supplied; diagnostics go to
stderr. Relative output paths resolve from the repository root. Do not commit raw
JSON: it contains source snippets. No login, token or platform upload is required.

For setup outside an application environment:

```sh
uv tool install --python 3.13 semgrep==1.170.0
```

Installation is setup, not a review action. Reviewers use the installed scanner
and report missing tools/network as blocked. Do not install, log in or weaken TLS
to make a review pass.

## Shared policy

[semgrep.sh](semgrep.sh) is the shared local/CI command. It uses the community
`p/python` and `p/typescript` Registry packs with the OSS engine. Metrics,
version checks and autofixes are disabled. Findings are advisory: no `--error`
or `--strict`; scanner/configuration failures retain their nonzero status.
A zero exit is not a security pass, and parser warnings remain coverage limits.
Semgrep's own rule metadata may label a finding “blocking”; this script does
not make findings fail CI. There are no custom rules or new suppressions.

Targets are `backend/app`, `code-execution/app` and `frontend/src`. Frontend
colocated tests are included. Python tests, specs, Dockerfiles, workflow/eval
code, dependency trees, credentials, database files and build outputs are outside
these roots. Normal Git/language/ignore filters still apply. This is neither a
dependency scan nor a whole-repository audit. Registry rules are downloaded and
can change independently of the CLI pin; record date, CLI/engine, rules and actual
coverage, and do not claim identical rule contents without a retained snapshot.

[Security CI](../../.github/workflows/security.yml) pins the CLI and runs this
same script for relevant PRs, master pushes and manual dispatch. JSON findings
remain in the job log; no findings artifact or Semgrep platform upload is added.
CI has not yet run. Branch protection is unchanged.

## Initial observed scan — 5 November 2026 (SGT)

Target: `190e98d8579dedb30d72408d94d9f2a1a6cf31e1`, application source unchanged
in the worktree. Command: `sh workflow/security/semgrep.sh /tmp/codeit-semgrep-initial.json`.
Semgrep 1.170.0, OSS engine, 225 rules (151 Python, 74 TypeScript).

- Exit 0; 106 files scanned: 33 backend Python, 10 executor Python, 63 frontend
  TypeScript/TSX. Of 110 candidate files, three backend prompt Markdown files and one frontend CSS file
  were not scanned; Python test directories were outside scope.
- Two findings, both `python.fastapi.security.wildcard-cors.wildcard-cors`:
  `backend/app/main.py:66` and `code-execution/app/main.py:62`.
- One `PartialParsing` warning at `backend/app/clients/llm.py:122`: the parser
  rejected an unparenthesized Python 3.14 multi-exception handler. Reported
  parsed-line coverage was approximately 99.9%. Manually inspect this gateway
  error-handling path on relevant changes; this is partial scanner coverage.
- The sandboxed version check failed with `ca-certs: empty trust anchors`.
  The approved run outside the sandbox succeeded without disabling TLS.
- Raw output is local at `/tmp/codeit-semgrep-initial.json` and may expire.

Both findings are confirmed pre-existing configuration risks, not introduced by
this setup. Backend and executor explicitly allow every origin; existing tests
also expect open CORS. Bearer authentication still applies, so these findings
alone do not demonstrate an authentication bypass. The executor should stay
private; backend browser origins and executor exposure need a deliberate
production policy. Follow up through matrix rows WEB-01 and EXEC-01 rather than
suppressing the findings or silently changing the product contract here.

This initial scan does not prove ownership enforcement, runtime isolation,
prompt-injection resistance, or deployed configuration. Matching source,
rules/engine and coverage are required before reusing this evidence.

References: [Semgrep CLI and exit behavior](https://docs.semgrep.dev/cli-reference),
[Python pack](https://semgrep.dev/p/python), [TypeScript pack](https://semgrep.dev/p/typescript).
