# Admin summary retained result — 13 November 2026

Status: IMPLEMENTED. User approved component-local UX improvement; no independent
review or deployment acceptance claimed. Baseline branch fix/admin-summary-live-rejection,
HEAD 6c5ae20; no tracked changes at start. Historical untracked artifacts preserved.
Applied implement-task project standards and vercel-react-best-practices guidance.

Changed files:
- frontend/src/features/admin/SummaryPage.tsx: retain the highest-ID observed success
  in component state; key panel by authenticated Admin ID and assignment ID. Current
  hooks remain authoritative for status, errors and disabling. Previous-result label
  uses original success timestamp and covers both statistics and summary. Status-read
  and request errors do not hide retained panels. Track which result a regeneration
  started from so a stale request error cannot label a later SSE success as previous.
- frontend/e2e/admin-summary.cjs: standalone mocked Playwright browser scenario.
- specs/frontend/frontend-admin.md: lifecycle, labels, isolation and remount limitation.
- This verification record.

No shared hooks, mergeJob, API types, auth behavior, backend or AI settings changed.
No production browser persistence or global result cache introduced. Test-only auth
storage follows the existing browser harness pattern. Every API call in the new
browser test is intercepted; neither backend nor provider is needed.

## Actual verification

All commands below ran in frontend unless specified otherwise.
- npm ci --ignore-scripts initially blocked by PowerShell npm.ps1 policy; npm.cmd
  invocation then failed in the sandbox with npm cache/log write failure. Approved
  escalated npm.cmd ci --ignore-scripts --fetch-retries=0 --fetch-timeout=15000
  succeeded (219 packages). Engine warning: installed Node 22.17.0 is below
  react-router's declared >=22.22.0. Audit reported 4 low/2 moderate advisories;
  no dependency or lockfile changes made and no audit fixes attempted.
- npm.cmd test: 13 files / 54 tests passed. These are existing Vitest tests;
  the new browser scenario runs separately.
- npm.cmd run lint: exit 0; three Fast Refresh export warnings in unchanged
  AuthProvider.tsx, EventsProvider.tsx and main.tsx.
- npm.cmd run build: exit 0, including tsc -b; Vite reports a >500 kB chunk warning.
- npm.cmd run format:check: exit 1, 76 unchanged files reported. No broad formatting.
- node node_modules/prettier/bin/prettier.cjs --check src/features/admin/SummaryPage.tsx e2e/admin-summary.cjs:
  passed on final code. Those two files were formatted with the corresponding --write command.
- node --check frontend/e2e/admin-summary.cjs from root: passed.
- git diff --check from root: passed (Git line-ending notices only).

Browser test execution: Vite launched with VITE_API_BASE_URL=http://127.0.0.1:5179
and empty VITE_API_FALLBACK_URL, via npm.cmd run dev -- --host 127.0.0.1 --port 5179 --strictPort.
Ran node e2e/admin-summary.cjs with PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH pointing to
C:/Program Files/Google/Chrome/Application/chrome.exe. Final scenario exit 0.
Earlier harness runs failed due to module URLs matching the API glob, exact-text
selectors containing nested Retry/account-role text; corrected test harness and reran.

Browser assertions cover initial success; running retains both panels and original
timestamp; success replaces both; late older success is ignored; failed regeneration;
status-read, network and request errors; first-generation failure without fallback;
assignment changes; account change with existing session/cache clearing; navigation
remount and refresh limitation; later SSE success after a request failure.

## Limitations and local reproduction

Retention ends when the panel unmounts, authenticated Admin changes, assignment
changes or the document reloads. A latest failed/running job cannot restore an older
stored success. No live AI, application database, production or multi-user server
testing performed. No commits, pushes, merges or deployment. Test Vite server stopped.

For reproduction, install locked dependencies with npm.cmd ci, then run npm.cmd test,
npm.cmd run lint and npm.cmd run build. Start the Vite command above in one PowerShell;
in another, set $env:PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH to an installed Chrome path
and run node e2e/admin-summary.cjs from frontend. This is a separate browser command,
not part of npm test. No backend or AI provider should be started for this scenario.
