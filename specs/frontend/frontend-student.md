# Frontend — Student

Pages for `role = student`. Endpoints: `specs/backend-spec.md` §5.4, §7.1, §7.4. State rules are in
`frontend-spec.md` §3–§4.

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

### 1.4 Editor state

- The editor content is **local state** of the question page (`useState`), not query data. It is
  set once by §1.2 when the page mounts (the page waits for the submissions query only when there
  is no draft) and after that changes only by typing or "Load into editor". Refetches of
  submissions (e.g. after a submit event) never touch it.
- Run, Submit and Hint send the editor's current content as `{code}`. An empty editor sends `"\n"`
  for hints (backend §5.4); Run / Submit are disabled when the editor is empty.
- Drafts are not synced live between two tabs on the same question; each tab saves what it has and
  the last save wins. This is acceptable for a convenience feature.

---

## 2. Pages

| Path | Shows | Queries |
|---|---|---|
| `/student` | Assignments grouped by class: title, due date (and "closed" when past), solved count "2 / 3" | `studentAssignments()` |
| `/student/assignments/:aid` | Description (`Markdown`), due date, questions with difficulty and a ✓ when `solved` | `studentAssignment(aid)` |
| `/student/assignments/:aid/questions/:qid` | Question page (§3) | `studentQuestion(aid, qid)`, `studentSubmissions(aid, qid)`, three `jobCheck`s |

`404` (e.g. removed from the class) → `NotFound`.

---

## 3. Question page

Two columns on wide screens (statement left, editor + panels right), stacked on narrow screens.

- **Statement**: title, difficulty, ✓ solved, limits, statement via `Markdown`, visible test cases
  (stdin / expected stdout, each with a copy button).
- **Editor** (§1) with three buttons: Run, Submit, Get hint.
- **Panels** (tabs): Run result, Submit result, Hint, Submissions.

The three jobs share one target key (backend §6.1) and are independent, so a hint and a run can be
in progress at the same time:

```ts
const tk = targetKey.question(aid, qid);           // "a{aid}:q{qid}"
const run = useJob("run", tk),    startRun = useStartJob<CodeIn>("run", tk);
const submit = useJob("submit", tk), startSubmit = useStartJob<CodeIn>("submit", tk);
const hint = useJob("hint", tk),  startHint = useStartJob<CodeIn>("hint", tk);
```

Clicking a button switches to its panel. Each button is disabled while its own job is
`in_process` (`frontend-spec.md` §4.5); the others stay usable.

### 3.1 Run and Submit results

Both render the judge result (backend §7.4) with one component:

- Header: verdict (colour-coded: `ACCEPTED` green, others red / amber), "passed / total",
  max time and memory. `error_message` when present.
- One row per test: index, status, time, memory. Visible tests can expand to show
  `stdout_preview` / `stderr_preview` next to the expected output from the statement. Hidden tests
  show "Hidden test" and only status / time / memory (the backend already removed the rest).
- A judged wrong answer is `success` with a non-accepted verdict; `failed` means the judge could not
  run and shows `error` (e.g. "The judge is busy. Try again in a moment.").
- Note under the header: "Result for the code sent at {created_at time}". The editor may have
  changed since; the result is not tied to the current text.

Submit specifics:

- Disabled with "Submissions closed" when `due_at` is past (browser clock). The backend's `409` is
  the authority and is shown inline if the clocks differ.
- When the submit job finishes, the job effects (`frontend-spec.md` §4.2) refetch the submissions
  list and `solved` flags, so the ✓ and the history update without extra code here.

### 3.2 Hint

- "Get hint" → `startHint.mutate({code})`. `422` from the injection guard (backend §8 #3) is shown
  inline as the backend's `detail` ("Your input contains text that looks like instructions to the
  AI…"); no job was created.
- `in_process` → "Thinking…". `success` → `result.hint_md` via `Markdown`, with a small line
  "Looked at: question, your code" from `result.tools_used`. `failed` → `error`.
- Only the latest hint is shown (the check endpoint returns the latest job).

### 3.3 Submissions

- Table from `studentSubmissions(aid, qid)`: time, verdict, passed / total, newest first.
- Clicking a row opens its code read-only (`studentSubmission(aid, qid, sid)`, `staleTime:
  Infinity` since submissions never change) with "Load into editor" (§1.3).
