# Frontend — Specification

The browser app for the coding-assignment app. It talks only to the backend
(`specs/backend-spec.md`).

---

## 1. Student code editor

### 1.1 Saving drafts

The editor's code is saved in `localStorage` so a refresh, closed tab or navigation does not lose
it. Drafts stay on that browser only.

- **Key:** `draft:{user_id}:{assignment_id}:{question_id}`, so students sharing a browser do not
  see each other's drafts.
- **Save:** on every edit, debounced by 1 s, and once more when leaving the page.
- **Value:** the code string. If `localStorage` is full or unavailable, skip saving and keep
  working; drafts are a convenience, not a guarantee.
- Drafts are **not** cleared on submit or logout; the draft is always the latest thing typed.

### 1.2 Loading the editor

When a question page opens, fill the editor from the first that exists:

1. The local draft (§1.1).
2. The code of the student's latest submission: `GET .../submissions` (newest first), then
   `GET .../submissions/{sid}` for the first entry.
3. Empty.

### 1.3 Past submissions

The submission history list can open any past submission's code (read-only, via
`GET .../submissions/{sid}`) with a "Load into editor" button. Loading replaces the editor
contents after a confirm, since it overwrites the draft.
