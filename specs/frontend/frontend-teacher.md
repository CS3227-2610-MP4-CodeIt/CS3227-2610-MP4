# Frontend — Teacher

Pages for `role = teacher`. Endpoints: `specs/backend-spec.md` §5.3, §7.2. State rules are in
`frontend-spec.md` §3–§4.

---

## 1. Pages

| Path | Shows | Queries |
|---|---|---|
| `/teacher` | Redirect to `/teacher/assignments` | — |
| `/teacher/questions` | Table of own questions: title, difficulty, topics, "AI" badge when `source_job_id` is set. "New question", "Generate with AI" | `teacherQuestions()` |
| `/teacher/questions/new` | Question form (§1.1), empty | — |
| `/teacher/questions/:id` | Question form seeded from the question; delete | `teacherQuestion(id)` |
| `/teacher/generate` | AI question generation (§2) | `jobCheck("question_gen", "-")`, `job(id)` per draft |
| `/teacher/assignments?class_id=` | Assignments of the teacher's classes, class filter in the URL. "New assignment" | `teacherClasses()`, `teacherAssignments(classId)` |
| `/teacher/assignments/new` | Assignment form (§1.2) | `teacherClasses()`, `teacherQuestions()` |
| `/teacher/assignments/:id` | Assignment view; edit form and delete only if the teacher created it | `teacherAssignment(id)`, `teacherQuestions()` |

### 1.1 Question form

Fields of `QuestionIn` (backend §5.3): title, statement (Markdown textarea with a preview tab using
`Markdown`), difficulty, topics (comma-separated, lower-cased and de-duplicated on blur), time
limit, memory limit, optional float tolerance (abs / rel).

Test cases: a list of rows (stdin textarea, expected stdout textarea, hidden checkbox) with add,
remove and move up / down. Client-side checks before sending, mirroring the backend so the teacher
gets instant feedback (the backend is still the authority):

- 2–50 test cases, at least one visible and one hidden.
- Title 1–200 chars, statement 1–20 000 chars, 0–5 topics of 1–30 chars.

Seeding for edit follows `frontend-spec.md` §3.5 (`key={id:updated_at}`). Server `422` items are
mapped to fields by `loc` (e.g. `["body", "test_cases", 3, "expected_stdout"]` → row 4).

### 1.2 Assignment form

Class (select from `teacherClasses()`, create only), title, description (Markdown), due date
(`datetime-local`, optional, sent as UTC ISO), and 1–3 distinct questions picked from own questions
in order (add / remove / reorder). `409` when removing a question that already has submissions →
`detail` inline.

On `/teacher/assignments/:id`, only the teacher who created the assignment may edit or delete it
(backend §3). `AssignmentOut` does not include the creator, so the controls are always shown and a
`404` on `PATCH` / `DELETE` is shown as "Only the teacher who created this assignment can change
it."

### 1.3 Mutations and cache updates

| Mutation | On success |
|---|---|
| Create question | `setQueryData(teacherQuestion(new.id))`; invalidate `teacherQuestions()`; navigate to it |
| Update question (`PUT`) | `setQueryData(teacherQuestion(id))`; invalidate `teacherQuestions()` and `["teacher", "assignment"]` (titles / difficulty shown there) |
| Delete question | `removeQueries(teacherQuestion(id))`; invalidate `teacherQuestions()`. `409` (used by an assignment) → inline |
| Create / update assignment | `setQueryData(teacherAssignment(id))`; invalidate `["teacher", "assignments"]` |
| Delete assignment | `removeQueries(teacherAssignment(id))`; invalidate `["teacher", "assignments"]`; navigate to the list |
| Approve draft (§2.3) | `setQueryData(teacherQuestion(new.id))`; invalidate `teacherQuestions()` |

---

## 2. AI question generation (`kind = question_gen`, `targetKey = "-"`)

The teacher has one generation stream (backend §6.1), so the page has one `jobCheck` entry:

```ts
const latest = useJob("question_gen", targetKey.none);
const start = useStartJob<QuestionGenIn>("question_gen", targetKey.none);
```

### 2.1 Layout

- **Request form**: difficulty, topics (1–5), prompt (1–2000 chars). "Generate" → `start.mutate`
  with `parent_job_id: null, feedback: null`. Disabled while a generation is `in_process`.
- **Draft view** (the selected draft, default: the latest job):
  - `in_process` → spinner "Generating… this can take a minute."
  - `success` → title, difficulty, topics, limits, statement via `Markdown`, test cases table
    (stdin / expected / hidden), and the reference solution in a read-only code block with a copy
    button. A warning line: "Expected outputs are written by the AI and may be wrong. Check them
    against the reference solution." (backend §7.2; the backend does not run them).
  - `failed` → `error` text.
- **Iterate box** under a successful draft: feedback textarea (1–2000 chars) + "Revise". Sends the
  original difficulty / topics / prompt with `parent_job_id = draft job id` and the feedback.
- **Approve** button under a successful, not yet approved draft (§2.3).
- **Draft history**: a list of earlier drafts in this session (§2.2); clicking one selects it.

### 2.2 Draft history state

The backend's check endpoint only returns the latest job, so the page remembers the ids of the
drafts it has seen:

- `sessionStorage["qgen:{user_id}"]` holds `{jobIds: number[], selectedId: number | null,
  prompt: string}`.
- An id is appended whenever `latest` (check query or `POST` response) has an id not yet in the
  list. So a draft started in another tab also shows up after its event.
- Each listed draft is read with `useQuery(keys.job(id))` (`GET /jobs/{id}`). Final drafts have
  `staleTime: Infinity` (`frontend-spec.md` §3.3), so the history costs one request per draft.
- When a new generation is started, `selectedId` moves to it.
- Revise reuses difficulty and topics from `result.draft` and the prompt from storage (the job
  result does not include the prompt). If the prompt is missing (new tab), the request form's
  prompt field must be filled first.

### 2.3 Approve

- Approved state is **derived**, not stored: a draft is approved when some question in
  `teacherQuestions()` has `source_job_id === job.id`. The page shows "Approved — open question"
  linking to it.
- `POST /teacher/question-generations/{job_id}/approve` → `201` question → cache updates in §1.3,
  then navigate to `/teacher/questions/{id}` so the teacher can fix test cases.
- `409` (already approved, e.g. from another tab) → invalidate `teacherQuestions()` so the derived
  state updates, and show "This draft was already approved."
