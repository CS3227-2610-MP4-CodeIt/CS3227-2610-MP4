# Manual, local-only evidence. Never mounts the repository, Docker socket or volumes.
# Run from repository root; scanner image/setup and Registry downloads need network.
[CmdletBinding()]
param([switch]$SnapshotOnly)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repo = (Get-Location).ProviderPath
$roots = @('backend/app', 'code-execution/app', 'frontend/src')
if (-not (Test-Path -LiteralPath (Join-Path $repo 'workflow/security/semgrep.sh'))) {
    throw 'Run from the repository root.'
}
$null = Get-Command git -ErrorAction Stop
$runId = 'admin-semgrep-' + [guid]::NewGuid().ToString('N')
$context = Join-Path ([IO.Path]::GetTempPath()) $runId
$evidence = Join-Path $repo ('workflow/planning/' + $runId)
$containerName = 'codeit-' + $runId
$imageTag = 'codeit-semgrep:' + $runId
$null = New-Item -ItemType Directory -Path $context, $evidence
$containerCreated = $false
$imageBuilt = $false
$evidenceSaved = $false
$exitCode = 2
$started = [Diagnostics.Stopwatch]::StartNew()
$record = [ordered]@{
    run_id = $runId; started_utc = [DateTimeOffset]::UtcNow.ToString('o')
    baseline_commit = $null; git_status = $null; outcome = 'setup_not_completed'
    container = $containerName; image_tag = $imageTag; image_id = $null
    docker_build_exit = $null; docker_start_exit = $null; container_exit = $null
    scanner_exit = $null; error = $null; cleanup_errors = @(); elapsed_seconds = $null
    snapshot_only = [bool]$SnapshotOnly
}

function Invoke-ScanDocker {
    param([string[]]$DockerArgs, [string]$LogName)
    $ErrorActionPreference = 'Continue'
    & docker @DockerArgs 2>&1 | Tee-Object -FilePath (Join-Path $evidence $LogName) | Out-Host
    return $LASTEXITCODE
}

try {
    $record.baseline_commit = (& git rev-parse HEAD | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Cannot identify repository revision.' }
    $record.git_status = (& git status --short --branch | Out-String).Trim()
    $files = @(& git ls-files --cached --others --exclude-standard -- $roots)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate scan sources.' }
    $files += @('workflow/security/semgrep.sh', '.gitignore')
    if (Test-Path -LiteralPath (Join-Path $repo '.semgrepignore')) { $files += '.semgrepignore' }
    $manifest = @()
    foreach ($file in ($files | Sort-Object -Unique)) {
        $isSource = $file -match '^(backend/app|code-execution/app|frontend/src)/.+\.(py|ts|tsx|css|md)$'
        $isControl = $file -in @('workflow/security/semgrep.sh', '.gitignore', '.semgrepignore')
        if ((-not $isSource -and -not $isControl) -or
            $file -match '(^|/)(\.env[^/]*|[^/]*(credential|secret|api[-_]?key)[^/]*)$|\.(db|sqlite|sqlite3)$|(^|/)\.\.(/|$)') {
            throw "Unexpected/sensitive snapshot path; inspect before proceeding: $file"
        }
        $source = Get-Item -LiteralPath (Join-Path $repo $file)
        if ($source.PSIsContainer) { throw "Directory supplied as file: $file" }
        $check = $source
        while ($check.FullName -ne $repo) {
            if ($check.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Symlink/reparse point rejected: $file" }
            $check = Get-Item -LiteralPath (Split-Path $check.FullName)
        }
        $text = [IO.File]::ReadAllText($source.FullName)
        # High-confidence check only: never print matched values. This is not a secrets audit.
        if ($text.IndexOf([char]0) -ge 0 -or
            $text -match '-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{30,}\b|\bsk-[A-Za-z0-9_-]{32,}\b') {
            throw "Potential sensitive/binary content; no Docker action allowed: $file"
        }
        $destination = Join-Path $context $file
        $null = New-Item -ItemType Directory -Force -Path (Split-Path $destination)
        Copy-Item -LiteralPath $source.FullName -Destination $destination
        $sourceHash = (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash
        if ($file -eq 'workflow/security/semgrep.sh') {
            [IO.File]::WriteAllText($destination, $text.Replace("`r`n", "`n"), (New-Object Text.UTF8Encoding($false)))
        }
        $snapshotHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
        if ($isSource -and $snapshotHash -ne $sourceHash) { throw "Source changed while snapshotting: $file" }
        $manifest += [pscustomobject]@{
            path = $file; source_sha256 = $sourceHash
            snapshot_sha256 = $snapshotHash
            kind = if ($isSource) { 'application_source' } else { 'scan_control' }
        }
    }
    foreach ($root in $roots) {
        if (@($manifest | Where-Object { $_.path.StartsWith($root + '/') }).Count -eq 0) {
            throw "Empty source root: $root"
        }
    }
    # Audit physical snapshot, not just the requested file list, before any Docker call.
    $actual = @(Get-ChildItem -LiteralPath $context -File -Recurse | ForEach-Object {
        $_.FullName.Substring($context.Length + 1).Replace('\', '/')
    })
    $unexpected = @(Compare-Object @($manifest.path | Sort-Object) @($actual | Sort-Object))
    if ($unexpected.Count -ne 0) { throw 'Snapshot inventory differs from the allowlist.' }
    $policy = Get-Content -LiteralPath (Join-Path $context 'workflow/security/semgrep.sh') -Raw
    foreach ($required in @('--config p/python --config p/typescript', '--oss-only --metrics off --disable-version-check --no-autofix', 'backend/app code-execution/app frontend/src')) {
        if (-not $policy.Contains($required)) { throw 'Shared scan policy changed; review before running.' }
    }
    if ($policy -match '(?m)\b(curl|wget|upload|login)\b|--config\s+auto|--pro\b|--trace\b|--autofix\b') {
        throw 'Unexpected network/platform/mutation behavior in shared scan policy; review required.'
    }
    ConvertTo-Json -InputObject $manifest -Depth 4 | Set-Content -LiteralPath (Join-Path $evidence 'source-manifest.json') -Encoding UTF8
    Copy-Item -LiteralPath (Join-Path $evidence 'source-manifest.json') -Destination (Join-Path $context 'source-manifest.json')
    $record.outcome = 'snapshot_validated'
    if ($SnapshotOnly) {
        $evidenceSaved = $true
        $exitCode = 0
    } else {
    $null = Get-Command docker -ErrorAction Stop
    # Diagnostic-only wrapper: the shared shell script remains the scan policy.
    # It adds rule timing/IDs and verbose skipped/parse diagnostics, not suppressions.
    @'
#!/usr/local/bin/python
import os
import sys

args = sys.argv[1:]
if args and args[0] == "scan":
    args += ["--verbose", "--time", "--max-log-list-entries=0"]
os.execv("/root/.local/bin/semgrep", ["semgrep", *args])
'@ | Set-Content -LiteralPath (Join-Path $context 'semgrep-diagnostics') -Encoding ascii
    @'
import csv
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOTS = ("backend/app", "code-execution/app", "frontend/src")
OUT = Path("/evidence")


def normalize(value):
    if not isinstance(value, str):
        return ""
    return value.removeprefix("/scan/").removeprefix("./")


def describe_scan(data, manifest, exit_code):
    candidates = {row["path"] for row in manifest if row["kind"] == "application_source"}
    paths = data.get("paths", {})
    scanned = {normalize(p) for p in paths.get("scanned", [])}
    raw_skips = paths.get("skipped", [])
    skipped = {normalize(p.get("path", "") if isinstance(p, dict) else p) for p in raw_skips}
    skipped.discard("")
    errors = data.get("errors", [])
    findings = data.get("results", [])
    def error_path(error):
        path = error.get("path", "")
        return normalize(path.get("value", "") if isinstance(path, dict) else path)
    components = {}
    for root in ROOTS:
        belongs = lambda p: p.startswith(root + "/")
        wanted = {p for p in candidates if belongs(p)}
        actual = {p for p in scanned if belongs(p)}
        ignored = {p for p in skipped if belongs(p)}
        components[root] = {
            "snapshot_files": sorted(wanted), "scanned_files": sorted(actual),
            "reported_skipped_files": sorted(ignored),
            "not_reported_scanned_or_skipped": sorted(wanted - actual - ignored),
            "snapshot_count": len(wanted), "scanned_count": len(actual),
            "reported_skipped_count": len(ignored),
            "errors_for_component": [error for error in errors if belongs(error_path(error))],
        }
    outcome = "scan_failed_or_partial" if exit_code else (
        "completed_with_findings" if findings else "completed_no_findings_reported"
    )
    return {
        "outcome": outcome, "scanner_exit": exit_code, "findings_count": len(findings),
        "components": components, "errors": errors, "raw_skipped_paths": raw_skips,
        "coverage_limitations": bool(errors or skipped or candidates - scanned),
        "note": "Exit zero is not acceptance. Unreported paths are not assumed scanned. Read parsing errors and diagnostics.",
    }


def main():
    manifest = json.loads(Path("source-manifest.json").read_text(encoding="utf-8-sig"))
    for row in manifest:
        actual = hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest()
        if actual.lower() != row["snapshot_sha256"].lower():
            raise RuntimeError("Snapshot hash mismatch: " + row["path"])
    version = subprocess.run(["semgrep", "--version"], text=True, capture_output=True)
    (OUT / "scanner-version.log").write_text(version.stdout + version.stderr)
    if version.returncode or version.stdout.strip() != "1.170.0":
        raise RuntimeError("Scanner version mismatch; no scan started")
    command = ["sh", "workflow/security/semgrep.sh", "/evidence/semgrep.json"]
    started = time.monotonic()
    with (OUT / "scan-stdout.log").open("w") as stdout, (OUT / "scan-stderr.log").open("w") as stderr:
        run = subprocess.run(command, stdout=stdout, stderr=stderr)
    execution = {
        "command": command, "scanner_exit": run.returncode,
        "seconds": time.monotonic() - started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "cli_version": version.stdout.strip(), "engine": "OSS",
        "configs": ["p/python", "p/typescript"],
        "diagnostic_additions": ["--verbose", "--time", "--max-log-list-entries=0"],
        "network": "Registry downloads enabled; no token/login, metrics/version checks disabled; no platform upload command",
    }
    (OUT / "execution.json").write_text(json.dumps(execution, indent=2))
    data = {}
    report_path = OUT / "semgrep.json"
    if report_path.exists():
        try:
            data = json.loads(report_path.read_text())
            if not isinstance(data, dict) or not (
                isinstance(data.get("paths"), dict)
                and isinstance(data.get("results"), list)
                and isinstance(data.get("errors"), list)
                and isinstance(data.get("version"), str)
            ):
                raise ValueError("Unexpected Semgrep JSON shape; coverage not established")
        except ValueError as error:
            (OUT / "json-error.txt").write_text(str(error))
            data = {}
    coverage = describe_scan(data, manifest, run.returncode)
    coverage["valid_json_report"] = bool(data)
    if not data:
        coverage["outcome"] = "scan_failed_no_valid_json"
    (OUT / "coverage.json").write_text(json.dumps(coverage, indent=2))
    rules = {
        "timing_rule_entries": data.get("time", {}).get("rules", []),
        "rules_by_engine": data.get("rules_by_engine", []),
        "skipped_rules": data.get("skipped_rules", []),
        "packs": execution["configs"],
        "note": "Preserved actual CLI rule entries and verbose diagnostics; no immutable Registry-content snapshot is claimed.",
    }
    rules["rule_entries_available"] = bool(rules["timing_rule_entries"] or rules["rules_by_engine"])
    if not rules["rule_entries_available"]:
        rules["coverage_limitation"] = "Rule IDs unavailable in JSON; inspect scan-stderr.log before accepting rule coverage."
    (OUT / "rules-used.json").write_text(json.dumps(rules, indent=2))
    with (OUT / "triage.csv").open("w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["rule", "path", "line", "severity", "disposition", "owner"])
        for finding in data.get("results", []):
            writer.writerow([finding.get("check_id"), finding.get("path"), finding.get("start", {}).get("line"),
                             finding.get("extra", {}).get("severity"), "NEEDS_REVIEW", ""])
    print(json.dumps(coverage), flush=True)
    return run.returncode if run.returncode else (0 if data else 2)


if __name__ == "__main__":
    raise SystemExit(main())
'@ | Set-Content -LiteralPath (Join-Path $context 'scan-driver.py') -Encoding ascii
    @'
FROM ghcr.io/astral-sh/uv:0.12.23 AS uv
FROM python:3.13-slim
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never SEMGREP_SEND_METRICS=off SEMGREP_ENABLE_VERSION_CHECK=0
RUN uv tool install --python /usr/local/bin/python semgrep==1.170.0
WORKDIR /scan
COPY . .
RUN mkdir /evidence && chmod 755 /scan/semgrep-diagnostics && ln -s /scan/semgrep-diagnostics /usr/local/bin/semgrep
CMD ["python", "/scan/scan-driver.py"]
'@ | Set-Content -LiteralPath (Join-Path $context 'Dockerfile') -Encoding ascii
    foreach ($generated in @('Dockerfile', 'scan-driver.py', 'semgrep-diagnostics')) {
        Copy-Item -LiteralPath (Join-Path $context $generated) -Destination $evidence
    }
    # Final context inventory includes only reviewed source/control files and our helpers.
    $allowed = @($manifest.path) + @('source-manifest.json', 'Dockerfile', 'scan-driver.py', 'semgrep-diagnostics')
    $actual = @(Get-ChildItem -LiteralPath $context -File -Recurse | ForEach-Object { $_.FullName.Substring($context.Length + 1).Replace('\', '/') })
    if (@(Compare-Object @($allowed | Sort-Object) @($actual | Sort-Object)).Count) { throw 'Unexpected final Docker context file.' }
    $record.docker_build_exit = Invoke-ScanDocker -DockerArgs @('build', '--progress', 'plain', '--tag', $imageTag, $context) -LogName 'build.log'
    if ($record.docker_build_exit -ne 0) { throw 'Scanner image setup failed; no scan executed.' }
    $imageBuilt = $true
    $record.image_id = (& docker image inspect --format '{{.Id}}' $imageTag | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Cannot preserve scanner image identity.' }
    $code = Invoke-ScanDocker -DockerArgs @('create', '--name', $containerName, '--network', 'bridge', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--memory', '2g', '--cpus', '2', $imageTag) -LogName 'create.log'
    if ($code -ne 0) { throw 'Cannot create disposable scanner.' }
    $containerCreated = $true
    $record.docker_start_exit = Invoke-ScanDocker -DockerArgs @('start', '--attach', $containerName) -LogName 'container.log'
    $state = & docker inspect --format '{{json .State}}' $containerName
    if ($LASTEXITCODE -ne 0) { throw 'Cannot preserve scanner state.' }
    $state | Set-Content -LiteralPath (Join-Path $evidence 'container-state.json')
    $stateObject = $state | ConvertFrom-Json
    if ($stateObject.Running -or $stateObject.Status -ne 'exited') { throw 'Scanner has not exited; retain resources.' }
    $record.container_exit = [int]$stateObject.ExitCode
    $code = Invoke-ScanDocker -DockerArgs @('cp', "${containerName}:/evidence/.", $evidence) -LogName 'copy.log'
    if ($code -ne 0) { throw 'Evidence copy failed; retain disposable resources.' }
    if (Test-Path -LiteralPath (Join-Path $evidence 'execution.json')) {
        $execution = Get-Content -LiteralPath (Join-Path $evidence 'execution.json') -Raw | ConvertFrom-Json
        $record.scanner_exit = [int]$execution.scanner_exit
    }
    if (Test-Path -LiteralPath (Join-Path $evidence 'coverage.json')) {
        $coverage = Get-Content -LiteralPath (Join-Path $evidence 'coverage.json') -Raw | ConvertFrom-Json
        $record.outcome = $coverage.outcome
    } else { $record.outcome = 'scanner_driver_failed_no_coverage_report' }
    $exitCode = $record.container_exit
    $evidenceSaved = $true
    }
} catch {
    $record.error = $_.Exception.Message
    Write-Warning $record.error
} finally {
    $record.elapsed_seconds = $started.Elapsed.TotalSeconds
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $evidence 'result.json') -Encoding UTF8
    if ($containerCreated -and $evidenceSaved) {
        $code = Invoke-ScanDocker -DockerArgs @('rm', $containerName) -LogName 'cleanup-container.log'
        if ($code -ne 0) { $record.cleanup_errors += 'Disposable container retained.' }
    } elseif ($containerCreated) { Write-Warning "Evidence incomplete; retained $containerName" }
    if ($imageBuilt -and (-not $containerCreated -or $evidenceSaved)) {
        $code = Invoke-ScanDocker -DockerArgs @('image', 'rm', $imageTag) -LogName 'cleanup-image.log'
        if ($code -ne 0) { $record.cleanup_errors += 'Disposable image tag retained.' }
    }
    $resolved = [IO.Path]::GetFullPath($context)
    $expected = [IO.Path]::GetFullPath((Join-Path ([IO.Path]::GetTempPath()) $runId))
    if ($resolved -eq $expected -and (Split-Path $resolved -Leaf) -eq $runId) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $evidence 'result.json') -Encoding UTF8
    Write-Host "Local evidence: $evidence"
    Write-Host 'Review findings, skipped paths and parsing errors; exit 0 alone is not acceptance.'
}
exit $exitCode
