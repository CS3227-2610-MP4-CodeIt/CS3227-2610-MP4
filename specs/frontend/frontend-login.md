# Frontend — Login and session

Shared state rules (auth storage, logout order, cross-tab sync) are in `frontend-spec.md` §5.
Backend endpoints: `specs/backend-spec.md` §4, §5.1.

---

## 1. Login page (`/login`)

- Form: username, password, "Log in" button (disabled while pending or a field is empty).
- `POST /auth/login` → store `{token, user}` (`frontend-spec.md` §5.1), `setQueryData(keys.me(),
  user)`, then navigate to `?next=` if it is a path under the user's own role, otherwise to the
  role home (`/admin`, `/teacher`, `/student`).
- `401` → "Invalid username or password." (the backend gives the same message for both cases;
  so does the UI). Password field is cleared, username kept.
- Logged-in users visiting `/login` are redirected to their home.
- No sign-up or password reset (backend §13).

## 2. Session restore (app start)

1. Read `localStorage["auth"]`. None → logged out.
2. Found → render with the stored `user` straight away (so the role guard and layout work at once),
   and run the `keys.me()` query (`GET /auth/me`) in the background.
3. `me` succeeds → replace the stored user with the fresh one (e.g. a changed display name).
   `me` returns `401` → `logoutLocal()` (`frontend-spec.md` §5.2).
4. The SSE stream (`frontend-spec.md` §4.1) opens as soon as a token is present.

## 3. Logout

The "Log out" button in the top bar calls `logout()` (`frontend-spec.md` §5.2): `POST /auth/logout`,
abort the stream, clear the query cache, clear storage, go to `/login`. Other open tabs follow via
the `storage` event.

Drafts in `localStorage` are kept on logout (`frontend-student.md` §1.1).
