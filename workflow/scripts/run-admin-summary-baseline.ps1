# Run manually from the repository root. Downloads images/locked dependencies.
# Does not use Compose, host mounts, env files, existing containers or volumes.
[CmdletBinding()]
param(
    [ValidateSet('Baseline', 'Supplemental', 'Regressions', 'Full', 'Quality')]
    [string]$Suite = 'Baseline',
    [switch]$PrepareBuildCache
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PrepareBuildCache -and $Suite -ne 'Quality') {
    throw '-PrepareBuildCache is supported only with -Suite Quality.'
}
$repo = (Get-Location).ProviderPath
if (-not (Test-Path -LiteralPath (Join-Path $repo 'backend/uv.lock'))) {
    throw 'Run this script from the repository root.'
}
$null = Get-Command docker -ErrorAction Stop
$null = Get-Command git -ErrorAction Stop
$runId = 'admin-summary-' + [guid]::NewGuid().ToString('N')
$containerName = 'codeit-' + $runId
$imageTag = 'codeit-admin-baseline:' + $runId
$context = Join-Path ([IO.Path]::GetTempPath()) $runId
$evidence = Join-Path $repo ('workflow/planning/' + $runId)
$null = New-Item -ItemType Directory -Path $context, $evidence
$started = [DateTimeOffset]::UtcNow
$timer = [Diagnostics.Stopwatch]::StartNew()
$containerCreated = $false
$built = $false
$evidenceSaved = $false
$scriptExit = 2
$record = [ordered]@{
    run_id = $runId; suite = $Suite; baseline_commit = $null; initial_git_status = $null
    started_utc = $started.ToString('o'); finished_utc = $null
    outcome = 'setup_error'; environment_error = $null
    container_name = $containerName; image_tag = $imageTag; image_id = $null
    python_image_id = $null; uv_image_id = $null
    pytest_exit_code = $null; tests = $null; passed = $null; failed = $null
    errors = $null; skipped = $null; build_seconds = $null; test_seconds = $null
    total_seconds = $null; cleanup_errors = @()
}
if ($PrepareBuildCache) {
    $record['prepare_build_cache'] = $true
    $record['docker_build_exit_code'] = $null
    $record['setup_build_exit_code'] = $null
    $record['offline_build_exit_code'] = $null
    $record['package_build_phase'] = 'not_started'
    $record['resolved_build_backend_versions'] = @()
}

function Invoke-DockerLog {
    param([string[]]$DockerArgs, [string]$LogPath)
    # Native stderr is evidence, not a PowerShell terminating error (PS 5.1).
    $ErrorActionPreference = 'Continue'
    & docker @DockerArgs 2>&1 | Tee-Object -FilePath $LogPath | Out-Host
    $code = $LASTEXITCODE
    return $code
}

try {
    $record.baseline_commit = (& git rev-parse HEAD | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Cannot record baseline commit.' }
    $record.initial_git_status = (& git status --short --branch | Out-String).Trim()
    $files = @(& git ls-files -- backend/app backend/tests)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate tracked source files.' }
    # Only code/prompt files from tracked trees, plus explicit project/test inputs.
    $files = @($files | Where-Object { $_ -match '\.(py|md)$' }) + @(
        'backend/pyproject.toml', 'backend/uv.lock', 'backend/backend-schema.sql',
        'backend/tests/test_admin_summary_reliability.py'
    )
    if (Test-Path -LiteralPath (Join-Path $repo 'backend/tests/test_admin_summary_validation.py')) {
        $files += 'backend/tests/test_admin_summary_validation.py'
    }
    $manifest = @()
    foreach ($file in ($files | Sort-Object -Unique)) {
        if ($file -notmatch '^backend/(app/|tests/|pyproject\.toml$|uv\.lock$|backend-schema\.sql$)' -or
            $file -match '(^|/)(\.env[^/]*|[^/]*(credential|secret|api[-_]?key)[^/]*)$|\.(db|sqlite|sqlite3)$|(^|/)\.\.(/|$)') {
            throw "Rejected context path: $file"
        }
        $source = Join-Path $repo $file
        # Reject reparse points at every level to prevent copying outside the allowlist.
        $check = Get-Item -LiteralPath $source
        while ($check.FullName -ne $repo) {
            if ($check.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Reparse point rejected: $file"
            }
            $check = Get-Item -LiteralPath (Split-Path $check.FullName)
        }
        $destination = Join-Path $context $file.Substring(8)
        $null = New-Item -ItemType Directory -Force -Path (Split-Path $destination)
        Copy-Item -LiteralPath $source -Destination $destination
        $manifest += [pscustomobject]@{ path = $file; sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash }
    }
    $manifest | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence 'context-manifest.json')
    @'
FROM ghcr.io/astral-sh/uv:0.12.23 AS uv
FROM python:3.14.4-slim
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /test
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --group dev --no-install-project
COPY backend-schema.sql ./
COPY app ./app
COPY tests ./tests
RUN mkdir /evidence
CMD ["/test/.venv/bin/python", "-m", "pytest", "-q", "-s", "-p", "no:cacheprovider", "tests/test_admin_summary_reliability.py", "--junitxml=/evidence/baseline.xml"]
'@ | Set-Content -LiteralPath (Join-Path $context 'Dockerfile') -Encoding ascii
    $testArguments = switch ($Suite) {
        'Baseline' { @('tests/test_admin_summary_reliability.py') }
        'Supplemental' { @('tests/test_admin_summary_validation.py') }
        'Regressions' { @('tests/test_admin.py', 'tests/test_guards.py', 'tests/test_jobs.py', 'tests/test_teacher.py', 'tests/test_student.py') }
        'Full' { @('tests') }
    }
    $command = @('/test/.venv/bin/python', '-m', 'pytest', '-q', '-s', '--tb=short', '-p', 'no:cacheprovider') + $testArguments + @('--junitxml=/evidence/baseline.xml')
    if ($Suite -eq 'Quality') {
        @'
import json
import subprocess
import time
from pathlib import Path

commands = [
    ["/test/.venv/bin/ruff", "format", "--check", "."],
    ["/test/.venv/bin/ruff", "check", "."],
    ["/test/.venv/bin/mypy", "app"],
    ["uv", "build", "--offline"],
]
results = []
for index, command in enumerate(commands):
    started = time.monotonic()
    run = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    Path(f"/evidence/quality-{index}.log").write_text(run.stdout)
    print("COMMAND", command, "EXIT", run.returncode, flush=True)
    print(run.stdout, flush=True)
    results.append({"command": command, "exit_code": run.returncode, "seconds": time.monotonic() - started})
Path("/evidence/quality.json").write_text(json.dumps(results, indent=2))
raise SystemExit(1 if any(row["exit_code"] for row in results) else 0)
'@ | Set-Content -LiteralPath (Join-Path $context 'quality.py') -Encoding ascii
        Add-Content -LiteralPath (Join-Path $context 'Dockerfile') -Value 'COPY quality.py /quality.py' -Encoding ascii
        $command = @('/test/.venv/bin/python', '/quality.py')
    }
    if ($PrepareBuildCache) {
        # Capture failures without failing the Docker layer, so logs/artifacts can
        # be extracted from a never-started disposable container before stopping.
        @'
import json
import re
import subprocess
import sys
import time
from pathlib import Path


def classify_build(exit_code, output):
    if exit_code == 0:
        return "package_build_pass"
    dependency_markers = (
        "Failed to resolve requirements from", "No solution found",
        "Failed to download", "Failed to fetch", "Network is unreachable",
        "Could not resolve host", "not found in the cache",
    )
    if any(marker.lower() in output.lower() for marker in dependency_markers):
        return "dependency_setup_failure"
    # A nonzero exit without a known dependency diagnostic is not proof that
    # project code is defective. Keep the traceback for human classification.
    return "build_failure_requires_log_review"


if __name__ == "__main__":
    command = ["uv", "build", "--verbose", "--out-dir", "/evidence/setup-dist"]
    started = time.monotonic()
    run = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    Path("/evidence/setup-build.log").write_text(run.stdout)
    # uv's verbose resolver reports selected requirements as name==version.
    # Record all observed backend selections, without guessing when absent.
    versions = sorted(set(re.findall(r"\bsetuptools==([0-9]+(?:\.[0-9A-Za-z]+)*(?:[+!-][0-9A-Za-z.]+)?)", run.stdout)))
    result = {
        "command": command, "exit_code": run.returncode,
        "classification": classify_build(run.returncode, run.stdout),
        "seconds": time.monotonic() - started,
        "python": sys.version,
        "uv": subprocess.check_output(["uv", "--version"], text=True).strip(),
        "declared_build_requirements": __import__("tomllib").loads(Path("pyproject.toml").read_text())["build-system"]["requires"],
        "resolved_setuptools_versions": versions,
        "version_evidence": "setup-build.log selected requirement entries" if versions else "unavailable; inspect verbose setup-build.log",
    }
    Path("/evidence/setup-build.json").write_text(json.dumps(result, indent=2))
    print(run.stdout, flush=True)
    print(json.dumps(result), flush=True)
    # Exit zero deliberately; the host checks the recorded build exit code
    # after extraction and aborts final Quality execution on setup failure.
'@ | Set-Content -LiteralPath (Join-Path $context 'prepare_build.py') -Encoding ascii
        Copy-Item -LiteralPath (Join-Path $context 'prepare_build.py') -Destination $evidence
        Add-Content -LiteralPath (Join-Path $context 'Dockerfile') -Encoding ascii -Value @'
COPY prepare_build.py /prepare_build.py
RUN python /prepare_build.py
'@
        $qualityPath = Join-Path $context 'quality.py'
        $qualitySource = Get-Content -LiteralPath $qualityPath -Raw
        $qualitySource = $qualitySource.Replace('["uv", "build", "--offline"]', '["uv", "build", "--offline", "--verbose", "--out-dir", "/evidence/offline-dist"]')
        $qualitySource | Set-Content -LiteralPath $qualityPath -Encoding ascii
        Copy-Item -LiteralPath $qualityPath -Destination $evidence
    }
    $dockerfile = Get-Content -LiteralPath (Join-Path $context 'Dockerfile')
    $dockerfile = @($dockerfile | Where-Object { $_ -notmatch '^CMD ' }) + ('CMD ' + (ConvertTo-Json -InputObject $command -Compress))
    $dockerfile | Set-Content -LiteralPath (Join-Path $context 'Dockerfile') -Encoding ascii
    Copy-Item -LiteralPath (Join-Path $context 'Dockerfile') -Destination $evidence
    $phase = [Diagnostics.Stopwatch]::StartNew()
    $code = Invoke-DockerLog -DockerArgs @('build', '--progress', 'plain', '--tag', $imageTag, $context) -LogPath (Join-Path $evidence 'build.log')
    $record.build_seconds = $phase.Elapsed.TotalSeconds
    if ($PrepareBuildCache) {
        $record.docker_build_exit_code = $code
        $record.package_build_phase = 'image_build'
    }
    if ($code -ne 0) { throw "Docker build failed (exit $code). No retry or additional setup attempted." }
    $built = $true
    $record.image_id = (& docker image inspect --format '{{.Id}}' $imageTag | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Cannot record test image ID.' }
    # Base tags may be absent locally with BuildKit; retain build log provenance too.
    foreach ($base in @('python:3.14.4-slim', 'ghcr.io/astral-sh/uv:0.12.23')) {
        $id = & docker image ls --no-trunc --quiet $base
        if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect base image identity.' }
        if ($base -like 'python:*') { $record.python_image_id = ($id | Out-String).Trim() }
        else { $record.uv_image_id = ($id | Out-String).Trim() }
    }
    $code = Invoke-DockerLog -DockerArgs @(
        'create', '--name', $containerName, '--network', 'none', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', '--memory', '1g', '--cpus', '2', $imageTag
    ) -LogPath (Join-Path $evidence 'create.log')
    if ($code -ne 0) { throw "Container creation failed (exit $code)." }
    $containerCreated = $true
    if ($PrepareBuildCache) {
        $code = Invoke-DockerLog -DockerArgs @('cp', "${containerName}:/evidence/.", $evidence) -LogPath (Join-Path $evidence 'copy-setup.log')
        if ($code -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $evidence 'setup-build.json'))) {
            throw 'Setup-build evidence unavailable; retain disposable resources.'
        }
        $setupResult = Get-Content -LiteralPath (Join-Path $evidence 'setup-build.json') -Raw | ConvertFrom-Json
        $record.setup_build_exit_code = [int]$setupResult.exit_code
        $record.resolved_build_backend_versions = @($setupResult.resolved_setuptools_versions)
        $record.package_build_phase = 'setup_build'
        if ($record.setup_build_exit_code -ne 0) {
            $record.outcome = $setupResult.classification
            $evidenceSaved = $true
            throw 'Setup-stage uv build failed; evidence saved, final Quality not started. See setup-build.json and setup-build.log.'
        }
        $record.package_build_phase = 'offline_quality'
    }
    $phase.Restart()
    $code = Invoke-DockerLog -DockerArgs @('start', '--attach', $containerName) -LogPath (Join-Path $evidence 'pytest.log')
    $record.test_seconds = $phase.Elapsed.TotalSeconds
    $state = & docker inspect --format '{{json .State}}' $containerName
    if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect disposable test state.' }
    $state | Set-Content -LiteralPath (Join-Path $evidence 'container-state.json')
    $stateObject = $state | ConvertFrom-Json
    if ($stateObject.Running -or $stateObject.Status -ne 'exited') { throw 'Test container did not exit normally; retain it for investigation.' }
    $record.pytest_exit_code = [int]$stateObject.ExitCode
    if ($Suite -eq 'Quality') {
        $record.pytest_exit_code = $null
        $code = Invoke-DockerLog -DockerArgs @('cp', "${containerName}:/evidence/.", $evidence) -LogPath (Join-Path $evidence 'copy.log')
        if ($code -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $evidence 'quality.json'))) {
            throw 'Quality evidence unavailable; retain container.'
        }
        $record.outcome = if ([int]$stateObject.ExitCode -eq 0) { 'quality_pass' } else { 'quality_check_failures' }
        if ($PrepareBuildCache) {
            $qualityResults = Get-Content -LiteralPath (Join-Path $evidence 'quality.json') -Raw | ConvertFrom-Json
            $record.offline_build_exit_code = [int]($qualityResults[-1].exit_code)
            $record.package_build_phase = if ($record.offline_build_exit_code -eq 0) { 'offline_build_pass' } else { 'offline_build_failed_requires_log_review' }
            $offlineLog = Get-Content -LiteralPath (Join-Path $evidence 'quality-3.log') -Raw
            if ($record.offline_build_exit_code -ne 0 -and $offlineLog -match '(?i)not found in the cache|Failed to resolve requirements from|No solution found') {
                $record.package_build_phase = 'offline_dependency_setup_failure'
            }
        }
        $scriptExit = [int]$stateObject.ExitCode
        $evidenceSaved = $true
    } else {
    $code = Invoke-DockerLog -DockerArgs @('cp', "${containerName}:/evidence/baseline.xml", (Join-Path $evidence 'baseline.xml')) -LogPath (Join-Path $evidence 'copy.log')
    if ($code -ne 0) { throw 'JUnit XML unavailable: setup/collection failure possible; retain container.' }
    [xml]$junit = Get-Content -LiteralPath (Join-Path $evidence 'baseline.xml') -Raw
    @($junit.SelectNodes('//testcase')) | ForEach-Object {
        $failureNode = $_.SelectSingleNode('failure')
        $errorNode = $_.SelectSingleNode('error')
        $skipNode = $_.SelectSingleNode('skipped')
        $caseOutcome = if ($null -ne $failureNode) { 'failed' }
            elseif ($null -ne $errorNode) { 'error' }
            elseif ($null -ne $skipNode) { 'skipped' } else { 'passed' }
        [pscustomobject]@{ case = $_.GetAttribute('name'); outcome = $caseOutcome; seconds = $_.GetAttribute('time') }
    } | Export-Csv -LiteralPath (Join-Path $evidence 'cases.csv') -NoTypeInformation
    $suites = @($junit.SelectNodes('//testsuite'))
    $record.tests = [int](($suites | ForEach-Object { [int]$_.tests } | Measure-Object -Sum).Sum)
    $record.failed = [int](($suites | ForEach-Object { [int]$_.failures } | Measure-Object -Sum).Sum)
    $record.errors = [int](($suites | ForEach-Object { [int]$_.errors } | Measure-Object -Sum).Sum)
    $record.skipped = [int](($suites | ForEach-Object { [int]$_.skipped } | Measure-Object -Sum).Sum)
    $record.passed = $record.tests - $record.failed - $record.errors - $record.skipped
    $countValid = if ($Suite -eq 'Baseline') { $record.tests -eq 18 } else { $record.tests -gt 0 }
    if ($countValid -and $record.errors -eq 0 -and $record.pytest_exit_code -in @(0, 1)) {
        $record.outcome = if ($record.failed) { 'baseline_assertion_failures' } else { 'baseline_pass' }
        $scriptExit = $record.pytest_exit_code
    } else {
        $record.outcome = 'test_setup_or_execution_error'
    }
    $evidenceSaved = $true
    }
} catch {
    $record.environment_error = $_.Exception.Message
    Write-Warning $record.environment_error
} finally {
    $record.finished_utc = [DateTimeOffset]::UtcNow.ToString('o')
    $record.total_seconds = $timer.Elapsed.TotalSeconds
    # Persist evidence before deleting any Docker resource.
    $record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidence 'result.json')
    @"
Outcome: $($record.outcome)
Baseline: $($record.baseline_commit)
Test image: $($record.image_id)
Tests: $($record.tests); passed: $($record.passed); failed: $($record.failed); errors: $($record.errors); skipped: $($record.skipped)
Pytest exit: $($record.pytest_exit_code)
Build seconds: $($record.build_seconds); test seconds: $($record.test_seconds)
Environment error: $($record.environment_error)
See pytest.log and baseline.xml for per-case assertion evidence. Null counts mean unavailable.
"@ | Set-Content -LiteralPath (Join-Path $evidence 'summary.txt')
    if ($containerCreated -and $evidenceSaved) {
        $cleanup = Invoke-DockerLog -DockerArgs @('rm', $containerName) -LogPath (Join-Path $evidence 'cleanup-container.log')
        if ($cleanup -ne 0) { $record.cleanup_errors += 'Container removal failed.' }
    } elseif ($containerCreated) {
        Write-Warning "Evidence incomplete; disposable container retained: $containerName"
    }
    if ($built -and (-not $containerCreated -or $evidenceSaved)) {
        $cleanup = Invoke-DockerLog -DockerArgs @('image', 'rm', $imageTag) -LogPath (Join-Path $evidence 'cleanup-image.log')
        if ($cleanup -ne 0) { $record.cleanup_errors += 'Test image removal failed.' }
    }
    # Verify the final absolute target before recursively deleting only our temp context.
    $resolvedContext = [IO.Path]::GetFullPath($context)
    $expectedContext = [IO.Path]::GetFullPath((Join-Path ([IO.Path]::GetTempPath()) $runId))
    if ($resolvedContext -eq $expectedContext -and (Split-Path $resolvedContext -Leaf) -eq $runId) {
        Remove-Item -LiteralPath $resolvedContext -Recurse -Force
    }
    $record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidence 'result.json')
    Write-Host "Evidence saved: $evidence"
    Write-Host 'Base images and Docker build cache are retained; no prune or volume cleanup is performed.'
}
exit $scriptExit
