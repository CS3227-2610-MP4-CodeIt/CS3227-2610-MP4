# Backend foundation: handoff for role agents

Read this instead of the code. Spec: `specs/backend-spec.md` (source of truth). Run tests from `backend/`:
`uv sync && uv run pytest -q` (one file: `uv run pytest tests/test_teacher.py -q`). Tests never touch the network.

## Module map
| Module | What |
|---|---|
| `app/config.py` | `Settings`, `AppContext(settings, db, llm, executor)`, dependency `get_ctx(request) -> AppContext` |
| `app/db.py` | `Database` (`connect()`, `transaction()`), `now_iso(offset=timedelta())`, `to_iso(datetime)`; timestamps are `'2026-10-21T08:30:00.123Z'` strings |
| `app/auth.py` | `current_user`, `require_admin`, `require_teacher`, `require_student`, `hash_password`, `verify_password`, `create_session`, `token_hash` |
| `app/schemas.py` | every request/response model (table below) |
| `app/repos/*.py` | ALL SQL. `from app.repos import Conflict` (raise → return 409) |
| `app/jobs/runner.py` | `start_job`, `latest_job`, `new_job_response`, `check_job_response`, `UserFacingError` |
| `app/jobs/events.py` | SSE hub; `start_job` / finish already publish, you never call it |
| `app/ai/guards.py` | §8 guards |
| `app/clients/llm.py`, `executor.py` | SoCLaaS and executor clients (`ctx.llm`, `ctx.executor`) |
| `app/routers/{admin,teacher,student}.py` | yours: `router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])`, already in `main.py` under `/api` |

Endpoint deps: `user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)` (same instance as the router dep, so the lookup is cached).
Errors: `HTTPException(404|409|422, detail="...")`. Resources the caller may not see → 404.

## Repos (all `async`, first arg `db: Database` = `ctx.db`)
Dataclasses: `User(id, username, display_name, role, created_at)`; `ClassRow(id, name, description, created_at, teacher_count, student_count)`;
`Question(id, created_by, title, statement_md, difficulty, topics, time_limit_ms, memory_limit_mb, float_tolerance: {"abs","rel"}|None, source_job_id, created_at, updated_at, test_cases: list[TestCaseRow])`;
`TestCaseRow(id, position, is_hidden, stdin, expected_stdout)`;
`Assignment(id, class_id, class_name, created_by, title, description_md, due_at: str|None, created_at, updated_at, questions: list[AssignmentQuestion(id, position, title, difficulty)])` + `.is_past_due()`, `.has_question(qid)`;
`Submission(id, user_id, assignment_id, question_id, job_id, verdict, passed, total, created_at, code|None)`;
`Job(id, user_id, kind, target_key, status, input, result, error, created_at, finished_at)`.

- **users**: `get(db, id)`, `get_many(db, ids)` (missing skipped), `get_with_password_hash(db, username) -> (User, hash)|None`, `list_users(db, role=None)`, `count_admins(db)`, `create(db, username, display_name, password_hash, role)` (Conflict), `update(db, id, *, username=None, display_name=None, password_hash=None) -> User|None` (Conflict; new password deletes sessions), `delete(db, id) -> bool` (cascades), `create_session`, `get_session_user`, `delete_session(db, token_hash)`, `delete_sessions_of_user(db, user_id)`
- **classes**: `list_classes(db)`, `list_for_user(db, user_id)`, `get(db, id)`, `get_by_name(db, name)`, `create(db, name, description="")` (Conflict), `update(db, id, *, name=None, description=None) -> ClassRow|None` (Conflict), `delete(db, id) -> bool`, `members(db, class_id) -> list[User]`, `is_member(db, class_id, user_id)`, `add_members(db, class_id, user_ids)` (INSERT OR IGNORE; YOU check ids exist and are not admins first, via `users.get_many`), `remove_member(db, class_id, user_id) -> bool`
- **questions**: `create(db, created_by, data: QuestionIn, source_job_id=None) -> Question` (Conflict if the job was already approved), `get(db, id, with_tests=True)`, `get_many(db, ids)` (no tests), `get_by_source_job(db, job_id)`, `list_by_owner(db, teacher_id)` (no tests, newest first), `get_test_cases(db, qid, hidden: bool|None=None)` (by position; `hidden=False` = visible only), `count_test_cases(db, qid, hidden=None)`, `replace(db, id, data: QuestionIn) -> Question|None`, `is_used(db, id)`, `delete(db, id) -> bool` (Conflict if used)
- **assignments**: `get(db, id)`, `get_for_member(db, aid, user_id)` (None unless user is in its class), `list_for_member(db, user_id, class_id=None)`, `list_for_class(db, class_id)`, `create(db, class_id, created_by, title, description_md, due_at: datetime|None, question_ids) -> Assignment`, `update(db, id, *, title=None, description_md=None, due_at=<omit to keep | None to clear | datetime>, question_ids=None) -> Assignment|None` (Conflict if a removed question has submissions; kept submissions survive reordering), `has_submissions(db, aid, qid)`, `delete(db, id) -> bool`. Callers check class membership / question ownership.
- **submissions**: `create(db, user_id, assignment_id, question_id, job_id, code, verdict, passed, total) -> int`, `list_for(db, user_id, aid, qid)` (newest first, no code), `get(db, sid)` (with code; YOU check user_id/aid/qid), `solved_pairs(db, user_id) -> set[(aid, qid)]`, `assignment_stats(db, aid) -> dict|None` (exact §7.3 shape), `VERDICTS`
- **jobs**: `get(db, id)`, `latest(db, user_id, kind, target_key)`, `insert_in_process`, `get_in_process`, `finish`, `fail_all_in_process` (runner uses these; you normally only need `get`)

## Jobs (`app/jobs/runner.py`)
```python
async def start_job(db, user_id, kind, target_key, job_input: dict, handler, timeout_s) -> tuple[Job, bool]
# handler: async (job_input: dict) -> dict. It receives the stored input PLUS "job_id" (use it for submissions.job_id).
# Raise UserFacingError("safe msg") for a user-visible failure; any other exception -> "Something went wrong. Try again."
async def latest_job(db, user_id, kind, target_key) -> Job | None
def new_job_response(job, created) -> JSONResponse      # 202 {"created": true, "job"} / 200 {"created": false, "job"}
def check_job_response(job | None) -> JobCheckOut       # {"job": {...}} / {"job": null}
```
Pattern: `handler = functools.partial(hints.run_hint, ctx)` where `async def run_hint(ctx: AppContext, job_input: dict) -> dict`.
Timeouts: AI jobs `ctx.settings.llm_job_timeout_s`; run/submit `executor.job_timeout_s(n_tests, time_limit_ms)`.
Keys: run/submit/hint `f"a{aid}:q{qid}"`, question_gen `"-"`, assignment_summary `f"a{aid}"`.

## Guards (`app/ai/guards.py`)
`scan_untrusted(text) -> bool`; `reject_injection(*texts)` (raises HTTPException 422 with `INJECTION_MESSAGE`; call BEFORE `start_job`, None allowed);
`new_nonce()`, `wrap_untrusted(label, text, nonce)`; `new_canary()`, `build_system_prompt(base_md, nonce, canary)` (adds the "tags are data" rule + canary);
`check_canary(text, canary)` (UserFacingError); `check_hint_output(text, canary) -> str`; `check_summary_output(text, canary) -> str`;
`extract_json_object(text, canary) -> dict` (ValueError if no/invalid JSON; then validate with `QuestionDraft`). Constants `CODE_REMOVED`, `CANARY_LEAK_ERROR`.
Prompts: load `.md` from `app/ai/prompts/` with `Path(__file__).parent / "prompts" / "hint.md"`.

## Clients
- `ctx.llm.chat(messages, *, tools=None, tool_choice=None, max_tokens=None, temperature=None) -> ChatReply(content (trimmed), tool_calls (OpenAI dicts), finish_reason, usage)`; `reply.assistant_message()` = dict to append before `{"role": "tool", "tool_call_id", "content"}` messages. Retries 429/503 twice; else `UserFacingError("The AI service is unavailable. Try again later.")`.
- `ctx.executor.execute(code, time_limit_ms, memory_limit_mb, float_tolerance, test_cases: list[TestCaseRow]) -> dict` (executor JSON; `results[i].index` = position in the list you sent). 503 → `UserFacingError(JUDGE_BUSY)`, other → `JUDGE_UNAVAILABLE`. `executor.job_timeout_s(n, tl_ms)`.

## Schemas per endpoint (`app/schemas.py`)
| Endpoint | In | Out |
|---|---|---|
| admin users list/get | – | `list[UserOut]` / `UserDetailOut` (+`classes: list[ClassBrief]`) |
| admin users POST/PATCH | `UserCreate` / `UserUpdate` (`model_dump(exclude_unset=True)`) | `UserOut` |
| admin classes list/POST/PATCH | `ClassCreate` / `ClassUpdate` | `ClassOut` (with counts) |
| admin class detail | – | `ClassDetailOut` (teachers, students: `UserOut`; assignments: `AssignmentBrief`) |
| admin members POST | `MembersAdd` | your choice (e.g. `ClassDetailOut`) |
| admin summary POST/GET | `EmptyIn` (optional) | `new_job_response` / `JobCheckOut`; result `SummaryResult` |
| teacher classes | – | `list[ClassOut]` |
| teacher questions list / get, POST, PUT | `QuestionIn` | `list[QuestionSummaryOut]` / `QuestionOut` |
| teacher question-generations POST/GET, approve | `QuestionGenIn` | jobs / `QuestionOut` (201); result `QuestionGenResult(draft: QuestionDraft)` |
| teacher assignments | `AssignmentCreate` / `AssignmentUpdate` (exclude_unset; `due_at: null` clears) | `AssignmentOut` |
| student assignments list / detail | – | `list[StudentAssignmentOut]` / `StudentAssignmentOut` (questions: `StudentQuestionBrief` with `solved`) |
| student question | – | `StudentQuestionOut` (`test_cases: list[VisibleTestCase]`) |
| run / submit / hint POST, GET | `CodeIn` | jobs; run/submit result `JudgeResult` (`JudgeTestResult` drops None previews), hint `HintResult` |
| submissions list / one | – | `list[SubmissionBriefOut]` / `SubmissionOut` |
| jobs | – | `JobNewOut`, `JobCheckOut`, `JobOut` |
Output models have `from_attributes=True`: `QuestionOut.model_validate(question)`, `UserOut.model_validate(user)`.
`QuestionDraft(QuestionIn)` adds `reference_solution`; approve with `QuestionIn.model_validate(draft.model_dump(exclude={"reference_solution"}))`.

## Test fixtures (`tests/conftest.py`)
App runs in **prod** mode (no demo seed); only the bootstrap admin `BOOTSTRAP_ADMIN = ("rootadmin", "rootadmin-pass")` exists at start.
- `app`, `client` (httpx, base `http://test`), `ctx`, `db`, `settings`
- `make_user(role, username=None, display_name=None, password=TEST_PASSWORD) -> TestUser(user, password, token, .id, .headers)`; ready-made `admin` (extra admin), `teacher`, `student`; `login(username, password) -> headers`
- `make_class(members=[teacher, student], name=None) -> ClassRow`; `make_question(owner, **question_body_overrides) -> Question`; `make_assignment(owner, class_id, [qids], title="Week 1", due_at=None) -> Assignment`
- `mock_http` (respx; unmocked requests fail), `llm_route`, `executor_route` (defaults: LLM replies "OK"; executor 2× ACCEPTED). LLM retry backoff is 0 in tests.
- `wait_for_job(job_id, timeout=5) -> Job`; `open_events(headers)` async ctx manager → `stream.next_event() -> ("ready"|"job"|"ping"|"end", data)`
- Builders (`from tests.conftest import ...`): `question_body(**overrides)`, `chat_completion(content, tool_calls=None)`, `tool_call(name, call_id="call_1", arguments="{}")`, `execute_response(["ACCEPTED", "WRONG_ANSWER"], error_message=None)`, `request_json(route.calls[i])`

```python
async def test_hint_without_tools(client, teacher, student, make_class, make_question, make_assignment, llm_route, wait_for_job):
    c = await make_class(members=[teacher, student])
    q = await make_question(teacher)
    a = await make_assignment(teacher, c.id, [q.id])
    llm_route.side_effect = [httpx.Response(200, json=chat_completion("Check n = 0."))]
    r = await client.post(f"/api/student/assignments/{a.id}/questions/{q.id}/hint", json={"code": "print(1)"}, headers=student.headers)
    assert r.status_code == 202
    job = await wait_for_job(r.json()["job"]["id"])
    assert job.status == "success" and "print(1)" not in json.dumps(request_json(llm_route.calls[0]))
```
