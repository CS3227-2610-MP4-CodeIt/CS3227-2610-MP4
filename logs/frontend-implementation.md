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
