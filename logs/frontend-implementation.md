# Frontend Implementation Log (login + admin)

App: `frontend/` (React 19.3 + Vite). Specs: `specs/frontend/frontend-spec.md`, `frontend-login.md`,
`frontend-admin.md`. Commit: `f5f1a5c` on `staging`.
Scope of this round: login/session and the admin pages. Teacher and student routes are guarded
placeholders ("not built yet").

## Process (spec-driven, single session)

1. Read the frontend specs plus the backend API (`backend-spec.md` §4–§7, `backend/app/schemas.py`,
   `routers/admin.py`, `routers/auth.py`) so the TS types match the real responses.
2. Built the **shared core first** (used by all three roles later), then login, then admin pages.
3. Checked with `tsc -b`, `oxlint`, Vitest, `vite build`, and a curl smoke test against a locally
   started backend (scratch DB): login, admin lists/detail, summary check, 422 shape, CORS preflight.
   No browser/UI tests (spec §9).
4. Spec changes requested during the session were written back to the spec so it stays the source
   of truth (see "Spec changes").

## What was built

| Area | Files | Notes |
|---|---|---|
| API | `api/client.ts`, `types.ts`, `keys.ts`, `queryClient.ts` | `apiFetch` (Bearer, JSON, `ApiError{status, detail}`); 401 → `logoutLocal` only if the rejected token is still current; all query keys in one place |
| Auth | `auth/session.ts`, `AuthProvider.tsx` | `localStorage["auth"]`; logout order: abort SSE → `queryClient.clear()` → remove storage; `/auth/me` refresh on start; cross-tab sync via `storage` event |
| SSE | `events/EventsProvider.tsx`, `reconcile.ts` | One `fetchEventSource` stream per tab; events only invalidate queries; backoff 1/2/5/10/15 s, reset on `ready`; 401 → logout |
| Jobs | `jobs/*` | `useJob` / `useStartJob` with the monotonic `mergeJob` rule; URLs from `(kind, target_key)` |
| Components | `components/*` | Layout (+ "Reconnecting…" bar after 3 s), RequireRole, QueryView, ErrorText/FieldError (422 list → per-field), ConfirmButton, Markdown (no raw HTML, images as links), JobStatusBadge, PasswordInput (eye toggle) |
| Login | `features/login/LoginPage.tsx` | Same message for unknown user / wrong password; `?next=` only within own role |
| Admin | `features/admin/*` | Users (role filter in URL, create, edit only changed fields, delete), classes (create → navigate, edit, members add/remove, delete), assignment AI summary (stats table + Markdown) |

## Decisions

- **No updated_at on users / classes** → edit forms are keyed on the editable fields instead of
  `id:updated_at`; same effect (remount after save, background refetch never overwrites typing).
- PATCH responses lack the nested lists (classes / members) → merged into the cached detail with
  `setQueryData(prev => ({...prev, ...res}))`.
- Token kept in a module variable in `session.ts` so `apiFetch` reads it synchronously, without
  React context.
- Shared Tailwind classes (`.btn`, `.input`, `.card`, …) via `@layer components` in `index.css`
  (spec allows only that one CSS file; no component library).

## Spec changes (asked for by the user)

- React Router v7 → **v8** (was pinned to v7 only because the spec said so; v8 needed no code changes).
- Backend URL from `frontend/.env` (git-ignored) with a committed `.env.example`
  (`VITE_API_BASE_URL=http://localhost:8000`, the backend container run locally) instead of
  `.env.development` / `.env.production`.
- Removed "(strict)" from the TypeScript line; tsconfigs stay at the Vite template defaults.

## Tests (Vitest, `npm test`) — 20 passing

`mergeJob` (older id / final→in_process / null), `keysToInvalidate` (submit, summary, ready, unknown
kind), `parseEvent`/`handleEvent` (bad JSON ignored, only the matching `jobCheck` invalidated),
`apiFetch` (Bearer, 204, 401 → logout, no logout on `/auth/login`, 422 list / 409 string kept),
session (abort before cache clear, storage removed, `keepStorage`, corrupt entry), `Markdown`
(`<script>`, `javascript:`, `<img>` not rendered).

## Issues hit

- `npm install react-router` pulled v8; pinned to v7 per spec, later moved to v8 at the user's request.
- Login smoke test failed at first: the bootstrap admin uses the `.env` password, not `demo1234`;
  reran with `BOOTSTRAP_ADMIN_PASSWORD` overridden on a scratch DB.
- oxlint flagged ref writes during render and `setState` in effects → moved ref updates into
  `useLayoutEffect`, the `/auth/me` user refresh into the query function, and status resets into
  effect cleanups. Two remaining warnings are hook exports next to providers (harmless).

## Next

Teacher and student pages (`frontend-teacher.md`, `frontend-student.md`), reusing `jobs/` and `events/`.

---

# Round 2 — Teacher pages

Spec: `specs/frontend/frontend-teacher.md`. Checked with `tsc -b`, `oxlint`, Vitest, `vite build`
and a read-only curl smoke test as `teacher1` (classes / questions / assignments / generation check,
422 shape). No spec changes.

## What was built (`src/features/teacher/`)

- `api.ts` — queries and mutations with the §1.3 cache updates (approve `409` → invalidate
  `teacherQuestions()`).
- Questions: list (AI badge), new / edit form with Markdown preview, topics normalised on blur,
  limits, optional float tolerance, test-case rows (add / remove / move / hidden), delete (`409` inline).
- `GeneratePage` — request form, draft view (status, statement, tests, reference solution + copy,
  AI-output warning), revise, approve (derived from `source_job_id`), session draft history.
- Assignments: list with `?class_id=` filter, new form (class + 1–3 ordered questions + local
  due date → UTC), detail with edit / delete only for `created_by === me` (`404` → creator message).
- Shared: `jobs/useJobById.ts` (`GET /jobs/{id}`, `staleTime: Infinity` once final),
  `toLocalInput` / `fromLocalInput` in `dates.ts`, teacher nav links, prefixes for assignment keys.

## Decisions

- Pure logic split out for unit tests: `questionForm.ts` (client checks, `toQuestionIn`, 422 `loc`
  → field / row mapping, `moveItem`) and `draftHistory.ts` (`sessionStorage["qgen:{user_id}"]`).
- Draft history: the latest job id is merged in at render (`withJob`) instead of `setState` in an
  effect; the effect only writes `sessionStorage`.
- Generate and Revise are two `useStartJob` instances on the same key so each shows its own error.
- Assignment `PATCH` sends only changed fields; clearing the due date sends `due_at: null`.
- Co-teachers see question titles without links (the questions are the creator's, so they would 404).

## Tests — 36 passing (+16)

`parseTopics`, `checkQuestion` (visible / hidden, 2–50 rows, title / statement / topics / limits /
tolerance), `toQuestionIn`, `questionErrors` (row / field / other), `moveItem`, draft history
(storage round-trip, corrupt entry, append once, start selects), `datetime-local` round-trip.

## Follow-up — co-teachers can read assignment questions (spec change asked for by the user)

- Specs: `backend-spec.md` §3 / §5.3 / §12.3, `frontend-spec.md` §3.2 key, `frontend-teacher.md` §1.
- Backend: `GET /teacher/assignments/{id}/questions/{qid}` → full `QuestionOut` for any teacher of
  the class; question not in the assignment / class not theirs → `404`. Test added (131 passing).
- Frontend: read-only page `/teacher/assignments/:id/questions/:qid`; co-teachers' question links
  go there, the creator's still go to the editor. Shared `QuestionPreview` (also used by draft view).
  The key sits under `["teacher", "assignment", aid]`, so question edits and assignment deletes
  already refresh / remove it.
