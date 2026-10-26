# Frontend — Specification

The browser app for the coding-assignment app. It talks only to the backend
(`specs/backend-spec.md`). This file covers what every page shares: the stack, the project layout,
and above all **how state is held and kept in sync with the server**, including SSE job
notifications. The pages of each role are in:

| File | Covers |
|---|---|
| `frontend-login.md` | Login, logout, session restore |
| `frontend-admin.md` | Users, classes, members, AI assignment summary |
| `frontend-teacher.md` | Questions, AI question generation, assignments |
| `frontend-student.md` | Assignments, code editor and drafts, run / submit / hint |

---

## 1. Stack

| Concern | Choice |
|---|---|
| Language / UI | TypeScript, **React 19.3** |
| Build | Vite (already set up in `frontend/`), `tsc -b` type check, `oxlint` |
| Styling | **Tailwind CSS v4** via `@tailwindcss/vite`; `@import "tailwindcss";` in `src/index.css`. `@tailwindcss/typography` (`prose`) for rendered Markdown. No other CSS files (delete `App.css`) |
| Server state | **TanStack Query v5** (`@tanstack/react-query`) — the only cache of server data |
| Routing | React Router v8 (declarative mode: `<BrowserRouter>`, `<Routes>`) |
| SSE | `@microsoft/fetch-event-source` (needed to send the `Authorization` header, backend §6.6) |
| Markdown | `react-markdown` + `remark-gfm`, **no** `rehype-raw` (raw HTML stays disabled, backend §8 #8) |
| Code editor | CodeMirror 6 via `@uiw/react-codemirror` + `@codemirror/lang-python` |
| Tests | Vitest, unit tests only (§9) |

The UI stays simple (assignment brief): a top bar with the user's name, role links and logout, and
plain pages of tables, forms and panels. No component library.

---

## 2. Project layout

```
frontend/src/
├── main.tsx                 # QueryClientProvider, BrowserRouter, AuthProvider, EventsProvider
├── App.tsx                  # routes (§7)
├── index.css                # @import "tailwindcss"; @plugin "@tailwindcss/typography";
├── api/
│   ├── client.ts            # apiFetch(): base URL, Bearer header, JSON, ApiError, 401 handling (§3.4)
│   ├── types.ts             # TS types mirroring backend/app/schemas.py
│   └── keys.ts              # every query key, built by functions (§3.2) — no inline key arrays elsewhere
├── auth/
│   └── AuthProvider.tsx     # token + user, login/logout, cross-tab sync (§5)
├── events/
│   ├── EventsProvider.tsx   # the one SSE connection per tab (§4.1)
│   └── reconcile.ts         # pure: event → which query keys to invalidate (§4.2)
├── jobs/
│   ├── types.ts             # Job, JobKind, result type per kind
│   ├── endpoints.ts         # (kind, targetKey) → check / new URL
│   ├── mergeJob.ts          # pure: monotonic job merge (§4.4)
│   ├── useJob.ts            # read a job "check" query
│   └── useStartJob.ts       # "new" mutation that writes into the check query
├── components/              # Layout, Markdown, JobStatusBadge, ErrorText, ConfirmButton, Spinner, NotFound
└── features/
    ├── login/  admin/  teacher/  student/   # pages, one folder per role
```

Rules: pages never call `fetch` directly (only `apiFetch` through a query or mutation); pages never
write query keys by hand (only `keys.ts`); job handling lives only in `jobs/` and `events/` and is
reused by all three roles (DRY).

---

## 3. State model

### 3.1 Where each kind of state lives

| State | Owner | Notes |
|---|---|---|
| Server data (users, classes, questions, assignments, submissions, jobs) | **TanStack Query cache** | Never copied into `useState` / context, except to seed an edit form (§3.5) |
| Auth (token, current user) | `AuthProvider` context + `localStorage["auth"]` | §5 |
| SSE connection status | `EventsProvider` context | `"connecting" \| "open" \| "reconnecting"` |
| Form inputs, open dialogs, selected tab | Component `useState` | Thrown away on navigation |
| Filters that should survive reload (e.g. role filter, class filter) | URL search params | So back / forward and refresh work |
| Student code drafts | `localStorage` | `frontend-student.md` §1 |
| Teacher's list of draft job ids | `sessionStorage` | `frontend-teacher.md` §2 |

There is no global store (Redux, Zustand…). With the server cache in TanStack Query, what is left is
small and local.

### 3.2 Query keys

All keys come from `api/keys.ts`. Each key starts with a role or `"job"` / `"jobCheck"` prefix so
whole groups can be invalidated at once.

```ts
export const keys = {
  me: () => ["me"],
  // admin
  adminUsers: (role?: Role) => ["admin", "users", { role }],
  adminUser: (id: number) => ["admin", "user", id],
  adminClasses: () => ["admin", "classes"],
  adminClass: (id: number) => ["admin", "class", id],
  // teacher
  teacherClasses: () => ["teacher", "classes"],
  teacherQuestions: () => ["teacher", "questions"],
  teacherQuestion: (id: number) => ["teacher", "question", id],
  teacherAssignments: (classId?: number) => ["teacher", "assignments", { classId }],
  teacherAssignment: (id: number) => ["teacher", "assignment", id],
  // student
  studentAssignments: () => ["student", "assignments"],
  studentAssignment: (aid: number) => ["student", "assignment", aid],
  studentQuestion: (aid: number, qid: number) => ["student", "question", aid, qid],
  studentSubmissions: (aid: number, qid: number) => ["student", "submissions", aid, qid],
  studentSubmission: (aid: number, qid: number, sid: number) => ["student", "submission", aid, qid, sid],
  // jobs
  jobCheck: (kind: JobKind, targetKey: string) => ["jobCheck", kind, targetKey],
  job: (id: number) => ["job", id],
} as const;
```

**`jobCheck` uses the backend's own `(kind, target_key)`** (backend §6.1: `"a12:q7"`, `"a12"`,
`"-"`). An SSE event carries exactly these two fields, so mapping an event to its cache entry needs
no parsing. Helpers in `jobs/endpoints.ts` build target keys (`targetKey.question(aid, qid)` →
`"a12:q7"`, `targetKey.assignment(aid)` → `"a12"`, `targetKey.none` → `"-"`) and URLs:

| kind | Check (`GET`) and new (`POST`) URL |
|---|---|
| `run` / `submit` / `hint` | `/student/assignments/{aid}/questions/{qid}/{kind}` |
| `question_gen` | `/teacher/question-generations` |
| `assignment_summary` | `/admin/assignments/{aid}/summary` |

### 3.3 Query defaults

```ts
new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: true,
      retry: (n, err) => !(err instanceof ApiError && err.status < 500) && n < 1,
    },
    mutations: { retry: false },
  },
});
```

- 4xx is never retried (a `404` means "gone or not yours", backend §4). Network / 5xx: one retry.
- `job(id)` queries for a **final** job (`success` / `failed`) use `staleTime: Infinity`: final jobs
  never change (backend §6.1).
- Only job state is pushed by the server. Other data (e.g. a teacher edits a question a student
  has open) is refreshed by `staleTime` + window focus; live updates for it are out of scope.

### 3.4 API client and errors

`apiFetch<T>(path, {method, body, signal})`:

- Prefixes `import.meta.env.VITE_API_BASE_URL` + `/api`; adds `Authorization: Bearer <token>` when
  logged in; sends and parses JSON; `204` → `undefined`. Passes the query's `signal` so cancelled
  queries abort their request.
- Non-2xx → throws `ApiError {status, detail}`. `detail` is either a string (e.g. `409`,
  injection guard `422`) or FastAPI's validation list; `ErrorText` shows a string as-is and a list
  as one line per item (`loc` last element: `msg`). Forms map list items to fields by `loc`.
- **`401` on any call except `/auth/login`** → `auth.logoutLocal()` (§5.2) and redirect to
  `/login`. The session is gone (expired, password changed, user deleted).

| Status | UI |
|---|---|
| `401` | Logged out (above) |
| `403` | Should not happen (routes are role-guarded); show "Not allowed" |
| `404` on a page's main query | `NotFound` component with a link home |
| `409`, `422` | Inline next to the form / button that caused it, using `detail` |
| Network / `5xx` | Inline "Could not reach the server. Try again." with a retry button |

### 3.5 Mutations (non-job writes)

- **Pessimistic**: wait for the server, then update the cache. No optimistic updates; every write is
  a quick SQLite call and server-side rules (`409`s) would make rollbacks common.
- On success: `setQueryData` for the detail key the response returns (when it returns the full
  object), then `invalidateQueries` for the list keys it affects. Each role file has the table.
- Buttons are disabled while `mutation.isPending` (no double submits).
- **Edit forms** are seeded once from query data: the form component is rendered with
  `key={`${id}:${updated_at}`}` and copies the data into `useState` on mount. A background refetch
  therefore never overwrites what the user is typing. After a successful save, the new
  `updated_at` remounts the form with the saved values.

---

## 4. Jobs and SSE reconciliation

The server is the single source of truth for jobs. SSE events only say **which** job changed
(backend §6.6); the client always re-reads the job through the API. Consequences the design relies
on:

- An event is a hint to refetch, so handling the same event twice, late, or out of order is harmless.
- A lost event only delays an update; `ready` (on every reconnect) triggers a full resync.
- No status ever comes from the event, so the client cannot show a state the server never had.

### 4.1 The connection (`EventsProvider`)

One stream per tab, opened when logged in, closed on logout:

```ts
fetchEventSource(`${base}/api/events`, {
  headers: { Authorization: `Bearer ${token}` },
  signal: controller.signal,            // aborted on logout / token change / unmount
  openWhenHidden: false,                 // close in background tabs; `ready` resyncs on return
  async onopen(res) {
    if (res.status === 401) throw new FatalAuthError();   // → logoutLocal(), no retry
    if (!res.ok) throw new RetryableError();
  },
  onmessage(msg) { handleEvent(queryClient, msg); },
  onclose() { throw new RetryableError(); },              // server ended the stream → reconnect
  onerror(err) {
    if (err instanceof FatalAuthError) throw err;          // stops the library's retry loop
    return nextBackoffMs();                                 // 1 s, 2 s, 5 s, 10 s, then 15 s
  },
});
```

- Backoff resets when a `ready` event arrives.
- The server ends the stream when the session expires (backend §6.6); the reconnect then gets
  `401` and the tab logs out.
- `openWhenHidden: false` keeps open connections to one per visible tab. Missing events while
  hidden is fine because reopening sends `ready`.
- Status is exposed as context; `Layout` shows a small "Reconnecting live updates…" bar when it
  has been `reconnecting` for more than 3 s.

### 4.2 Handling events (`events/reconcile.ts`)

`reconcile.ts` is a pure function so it can be unit-tested without a server:

```ts
type ServerEvent =
  | { type: "ready" }
  | { type: "job"; job_id: number; kind: JobKind; target_key: string };

export function keysToInvalidate(ev: ServerEvent): QueryKey[] {
  if (ev.type === "ready") return [["jobCheck"], ["job"], ...ALL_JOB_EFFECT_PREFIXES];
  if (!isJobKind(ev.kind)) return [];                       // unknown kind: ignore
  return [
    keys.jobCheck(ev.kind, ev.target_key),
    keys.job(ev.job_id),
    ...jobEffects(ev.kind, ev.target_key),
  ];
}

export function handleEvent(qc: QueryClient, msg: EventSourceMessage) {
  const ev = parse(msg);                                    // bad JSON / unknown event → ignore
  if (!ev) return;
  for (const queryKey of keysToInvalidate(ev)) qc.invalidateQueries({ queryKey });
}
```

`invalidateQueries` refetches only queries that are **mounted** (active) and marks the rest
stale, so an event for a page the user is not on costs nothing now and is fetched fresh when
they open it. A key that is not in the cache is a no-op. Final jobs in `job(id)` have
`staleTime: Infinity` but invalidation still refetches them; this is harmless (same data) and keeps
the rule simple.

**Job effects** — other data a job changes, invalidated together with the job:

| kind | Also invalidate | Why |
|---|---|---|
| `submit` (`a{aid}:q{qid}`) | `studentSubmissions(aid, qid)`, `studentQuestion(aid, qid)`, `studentAssignment(aid)`, `studentAssignments()` | A submission row and maybe a new `solved` flag (the backend writes the row before marking the job `success`, backend §7.4, so the refetch after the "finished" event sees it) |
| `run`, `hint`, `question_gen`, `assignment_summary` | — | Only the job itself changes |

Effects run on both the "created" and the "finished" event because the event does not say which
one it is. The extra refetch on "created" is one cheap GET, and it avoids tracking transitions.

`ALL_JOB_EFFECT_PREFIXES` for `ready` is `[["student", "submissions"], ["student", "question"],
["student", "assignment"], ["student", "assignments"]]`.

### 4.3 Reading a job (`useJob`)

```ts
function useJob(kind: JobKind, targetKey: string) {
  return useQuery({
    queryKey: keys.jobCheck(kind, targetKey),
    queryFn: async ({ signal }) => {
      const next = await apiFetch<JobCheckOut>(checkUrl(kind, targetKey), { signal });
      const prev = queryClient.getQueryData<JobCheckOut>(keys.jobCheck(kind, targetKey));
      return mergeJob(prev, next);
    },
  });
}
```

The page shows `data.job` (or the empty state when `null`). It never polls: updates come from
events (§4.2), `ready`, mount and window focus.

### 4.4 Merge rule (`mergeJob`)

Two writers fill a `jobCheck` entry: the check query (`GET`) and the new-job mutation (`POST`,
§4.5). Their responses can arrive in any order, so writes go through one monotonic rule:

```ts
export function mergeJob(prev: JobCheckOut | undefined, next: JobCheckOut): JobCheckOut {
  const p = prev?.job, n = next.job;
  if (!p) return next;
  if (!n) return prev!;                                   // never go back to "no job"
  if (n.id < p.id) return prev!;                          // older job: stale response
  if (n.id === p.id && isFinal(p.status) && n.status === "in_process") return prev!;
  return next;
}
```

- Job ids are increasing (SQLite `INTEGER PRIMARY KEY`), and the latest job per key is the one with
  the highest id. So "higher id wins, and a job never goes from final back to `in_process`"
  is exactly the backend state machine (§6.1).
- Example it fixes: a check request starts while job 42 is `success`; the user clicks Run; the
  `POST` returns job 43 `in_process` and is written; then the slow check returns job 42. Without
  the rule the panel would jump back to 42's old result.

### 4.5 Starting a job (`useStartJob`)

```ts
function useStartJob<Body>(kind: JobKind, targetKey: string) {
  const qc = useQueryClient();
  const key = keys.jobCheck(kind, targetKey);
  return useMutation({
    mutationFn: (body: Body) => apiFetch<JobNewOut>(newUrl(kind, targetKey), { method: "POST", body }),
    onSuccess: async (res) => {
      await qc.cancelQueries({ queryKey: key });          // drop an in-flight check
      qc.setQueryData<JobCheckOut>(key, (prev) => mergeJob(prev, { job: res.job }));
    },
  });
}
```

- The UI shows `in_process` straight from the `POST` response; it does not wait for the "created"
  event.
- **`created: false`** (a job for this key is already running, maybe from another tab): the
  returned job is shown like any other, plus a one-line notice under the button, e.g. "A run is
  already in progress — showing it. Your latest code was not sent." (the backend ignored the body).
- The start button is disabled while `isPending` **or** the cached job is `in_process`. This is
  only for UX; the backend dedups anyway (backend §6.3).
- `422` (validation or injection guard) and `409` (e.g. submit after due date) are shown inline;
  no job was created, so the cache is untouched.

### 4.6 Scenarios

| Scenario | What happens |
|---|---|
| Normal: click Run, job finishes | `POST` → `in_process` shown. "created" event → refetch (same job). "finished" event → refetch → `success` shown |
| "finished" event arrives before the `POST` response | Refetch returns 43 `success`; then `POST` result 43 `in_process` is merged → rule keeps `success` |
| Two tabs, same student, same question | Each tab has its own stream; backend sends events to both. The tab that didn't click refetches and shows the job too. A click in the second tab gets `created: false` and the notice |
| Tab closed while a hint runs, reopened later | Page mounts → check returns the job (`in_process` or final). Events take over from there |
| Stream drops while a job runs | Bar shows "Reconnecting…". On reconnect `ready` → all `jobCheck` / `job` / effect queries invalidated → current state fetched |
| Event dropped by the server (full queue, backend §6.6) | Corrected at the next `ready`, window focus, or remount |
| Event for a page not open | `invalidateQueries` marks it stale; no request until the page opens |
| Server restart | Stream closes → reconnect → `ready` → check shows the job as `failed` "Interrupted by a server restart" |
| Session expired / user deleted / password changed | Next API call or stream reconnect → `401` → logout |
| User navigates away mid-job | Query unmounts; job keeps running on the server; cache entry stays until GC (5 min default) and is refreshed when the page opens again |

### 4.7 Job display (`JobStatusBadge` + per-feature panels)

| `job` | Shows |
|---|---|
| `null` | Feature's empty state (e.g. "No hint yet") |
| `in_process` | Spinner + "Running…" / "Thinking…" and elapsed time since `created_at` |
| `success` | Feature result (per role file) + "finished {relative time}" |
| `failed` | `error` text (already user-safe, backend §6.4) in red + the start button stays available |

---

## 5. Auth state

### 5.1 Storage

- `localStorage["auth"] = JSON {token, user}` after login, so all tabs share one login and a
  refresh keeps it. Wrapped in try/catch; if storage is unavailable the login lasts until the tab
  closes.
- The token is sent only in the `Authorization` header (API and SSE), never in a URL.
- XSS is what could steal it; Markdown is rendered without raw HTML (§6) and nothing uses
  `dangerouslySetInnerHTML`.

### 5.2 Logout and user switch

`logoutLocal()` (used by logout, `401`, and cross-tab sync), in this order:

1. Abort the SSE stream (so no event lands in the cache after it is cleared).
2. `queryClient.clear()` — query keys do not contain the user id, so the cache **must** be emptied
   before another user logs in on the same tab.
3. Remove `localStorage["auth"]`, set auth context to logged out, navigate to `/login`.

`logout()` first calls `POST /auth/logout` (ignoring errors), then `logoutLocal()`.

**Cross-tab:** `AuthProvider` listens to the `storage` event on `"auth"`. Removed → `logoutLocal()`.
Changed to a different token (another login in another tab) → `logoutLocal()` then adopt the new
auth (fresh cache, new stream).

Details of the login page and session restore are in `frontend-login.md`.

---

## 6. Shared components

- **`Markdown`** — `react-markdown` + `remark-gfm` inside `prose`. Raw HTML is not rendered. Links:
  the default `urlTransform` (drops `javascript:` etc.), and `target="_blank" rel="noopener
  noreferrer"`. Images are rendered as links, not loaded. Used for every statement, hint and summary.
- **`ConfirmButton`** — a button that asks `confirm()` first; used for every delete.
- **`Layout`** — top bar (app name, role nav, user display name, logout), SSE status bar, `<Outlet/>`.
- Dates: backend sends UTC ISO strings; show them in the browser's local time
  (`Intl.DateTimeFormat`). `datetime-local` inputs are converted to UTC ISO before sending.

---

## 7. Routing

| Path | Page | Guard |
|---|---|---|
| `/login` | Login | Logged out only (logged in → own home) |
| `/admin/...` | `frontend-admin.md` | `role = admin` |
| `/teacher/...` | `frontend-teacher.md` | `role = teacher` |
| `/student/...` | `frontend-student.md` | `role = student` |
| `/` and unknown paths | Redirect to own home (`/admin`, `/teacher`, `/student`) or `/login` | — |

`RequireRole` wraps each role's routes: not logged in → `/login?next=<path>`; wrong role → own home.
The backend still checks every call; the guard is only for UX.

---

## 8. Configuration and build

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Backend origin without `/api`. Default `http://localhost:8000` (the backend Docker container run locally) |

The value is read from `frontend/.env` (git-ignored). `frontend/.env.example` is committed with the
default; copy it to `.env` and change the URL to point at another backend.

`npm run build` outputs a static `dist/` that is deployed to any static host (with fallback to
`index.html` for client-side routes). The URL is baked in at build time, so set `.env` before
building for production.

---

## 9. Tests

Vitest **unit tests only**, on the state logic, with `fetch` mocked. No UI tests: no rendering
pages and clicking through them, no browser / end-to-end tests (Playwright, Cypress, React Testing
Library).

| Case | Expected |
|---|---|
| `mergeJob`: older id after newer | Keeps newer |
| `mergeJob`: same id, `success` then `in_process` | Keeps `success` |
| `mergeJob`: `null` after a job | Keeps the job |
| `keysToInvalidate` for a `submit` event | `jobCheck`, `job`, submissions, question, assignment(s) keys |
| `keysToInvalidate` for `ready` | All job prefixes + effect prefixes |
| Unknown event / kind / bad JSON | Ignored, no throw |
| `handleEvent` on a `QueryClient` holding a stale job | That `jobCheck` query is invalidated; unrelated keys untouched |
| `apiFetch` gets `401` | Calls `logoutLocal`; throws `ApiError` |
| `apiFetch` gets `422` list / `409` string | `ApiError.detail` keeps the shape |
| `logoutLocal` | Stream aborted before cache cleared; `auth` removed from storage |
| `Markdown` output (`renderToStaticMarkup`) with `<script>` / `javascript:` link | Not rendered / link removed (security check, backend §8 #8) |

---

## 10. Out of scope

- Live updates for non-job data (other users' edits); covered by refetch on focus.
- Offline support, service workers, i18n, dark mode.
- Logging, analytics, error reporting services.
- UI and end-to-end tests (§9).
