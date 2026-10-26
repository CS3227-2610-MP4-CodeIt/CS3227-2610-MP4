# Frontend — Admin

Pages for `role = admin`. Endpoints: `specs/backend-spec.md` §5.2. State rules (query keys,
pessimistic mutations, job hooks) are in `frontend-spec.md` §3–§4.

---

## 1. Pages

| Path | Shows | Queries |
|---|---|---|
| `/admin` | Redirect to `/admin/users` | — |
| `/admin/users?role=` | Table: username, display name, role. Role filter (all / teacher / student / admin) in the URL. "New user" form | `adminUsers(role)` |
| `/admin/users/:id` | Edit form (username, display name, new password), classes the user is in, delete | `adminUser(id)` |
| `/admin/classes` | Table: name, teacher count, student count. "New class" form | `adminClasses()` |
| `/admin/classes/:id` | Edit name / description, teachers and students lists (remove buttons), "Add members" picker, assignments list (each links to its summary), delete | `adminClass(id)` |
| `/admin/classes/:cid/assignments/:aid` | AI summary of one assignment (§2). Title and due date come from the class detail's assignment list | `adminClass(cid)`, `jobCheck("assignment_summary", "a{aid}")` |

### 1.1 Forms

- New user: username, display name, password, role (teacher / student only; admins come from the
  bootstrap, backend §5.2). `409` → "Username already taken" inline.
- Edit user: only changed fields are sent in the `PATCH`. Password field blank = unchanged. The UI
  notes that changing a password logs that user out; changing **your own** password logs you out
  too (the next call gets `401`, `frontend-spec.md` §3.4).
- Delete user / class: `ConfirmButton`. `409` (last admin, self) → `detail` shown inline.
- Add members: a multi-select list built from `adminUsers()` (teachers and students only) minus
  current members, filtered by a search box. Sends `{user_ids}` in one `POST`.

### 1.2 Mutations and cache updates

| Mutation | On success |
|---|---|
| Create user | invalidate `["admin", "users"]` |
| Update user | `setQueryData(adminUser(id))` with the response; invalidate `["admin", "users"]` and `["admin", "class"]` (names shown in member lists) |
| Delete user | `removeQueries(adminUser(id))`; invalidate `["admin", "users"]`, `["admin", "classes"]`, `["admin", "class"]`; navigate to the list |
| Create class | invalidate `adminClasses()`; navigate to the new class |
| Update class | `setQueryData(adminClass(id))`; invalidate `adminClasses()` |
| Delete class | `removeQueries(adminClass(id))`; invalidate `adminClasses()` and `["admin", "user"]`; navigate to the list |
| Add / remove member | invalidate `adminClass(id)`, `adminClasses()` (counts) and `["admin", "user"]` (their class lists) |

`["admin", "users"]` etc. are prefixes covering every role filter / id (built by `keys.ts`).

---

## 2. AI assignment summary (`kind = assignment_summary`)

Uses the shared job hooks with `targetKey = "a{aid}"`:

```ts
const job = useJob("assignment_summary", targetKey.assignment(aid));
const start = useStartJob<{}>("assignment_summary", targetKey.assignment(aid));
```

- Button "Generate summary" (or "Regenerate" when a job exists) → `start.mutate({})`. Disabled while
  the job is `in_process` (`frontend-spec.md` §4.5).
- `in_process` → spinner "Summarising…". The admin can leave the page; the result is there when
  they come back (check on mount).
- `success` → two parts side by side (stacked on narrow screens), as backend §7.3 requires:
  - **Stats table** from `result.stats`: header line with students in class / attempted any /
    solved all; one row per question: position, title, difficulty, attempted, correct, total
    submissions, and the verdict counts.
  - **Summary** from `result.summary_md` via `Markdown`, labelled "AI summary — check against the
    numbers".
- `failed` → `error` text and the button.
- The summary is not refreshed automatically when new submissions arrive; the admin regenerates it.
