"""Request / response models for every endpoint (spec §5, §7). Routers import from here only."""

from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
    model_validator,
)

MAX_CODE_BYTES = 64 * 1024
MAX_IO_BYTES = 1024 * 1024

Role = Literal["admin", "teacher", "student"]
MemberRole = Literal["teacher", "student"]
Difficulty = Literal["easy", "medium", "hard"]
JobKind = Literal["run", "submit", "hint", "question_gen", "assignment_summary"]
JobStatus = Literal["in_process", "success", "failed"]
Verdict = Literal["ACCEPTED", "WRONG_ANSWER", "TIME_LIMIT_EXCEEDED", "MEMORY_LIMIT_EXCEEDED", "RUNTIME_ERROR"]

USERNAME = {"min_length": 3, "max_length": 32, "pattern": r"^[A-Za-z0-9_.-]+$"}
DISPLAY_NAME = {"min_length": 1, "max_length": 100}
PASSWORD = {"min_length": 8, "max_length": 128}


def _check_bytes(value: str, limit: int) -> str:
    if len(value.encode()) > limit:
        raise ValueError(f"must be at most {limit} bytes")
    return value


def _check_code(value: str) -> str:
    if "\x00" in value:
        raise ValueError("must not contain NUL bytes")
    return _check_bytes(value, MAX_CODE_BYTES)


def _normalize_topics(topics: list[str]) -> list[str]:
    """Strip, lower-case and de-duplicate (keeping order)."""
    seen: list[str] = []
    for topic in topics:
        t = topic.strip().lower()
        if not 1 <= len(t) <= 30:
            raise ValueError("each topic must be 1-30 characters")
        if t not in seen:
            seen.append(t)
    return seen


class OutModel(BaseModel):
    """Response models can be built from repo dataclasses: `UserOut.model_validate(user)`."""

    model_config = ConfigDict(from_attributes=True)


# --- health / auth (§5.1, §5.5) ---------------------------------------------


class HealthOut(BaseModel):
    status: Literal["ok"] = "ok"


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class UserOut(OutModel):
    id: int
    username: str
    display_name: str
    role: Role


class LoginOut(BaseModel):
    token: str
    user: UserOut


# --- admin: users (§5.2) ----------------------------------------------------


class UserCreate(BaseModel):
    username: str = Field(**USERNAME)
    display_name: str = Field(**DISPLAY_NAME)
    password: str = Field(**PASSWORD)
    role: MemberRole  # admins only via bootstrap


class UserUpdate(BaseModel):
    """PATCH: use `body.model_dump(exclude_unset=True)`."""

    username: str | None = Field(default=None, **USERNAME)
    display_name: str | None = Field(default=None, **DISPLAY_NAME)
    password: str | None = Field(default=None, **PASSWORD)

    @field_validator("username", "display_name", "password")
    @classmethod
    def _not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("must not be null")
        return value


class ClassBrief(OutModel):
    id: int
    name: str


class UserDetailOut(UserOut):
    """GET /admin/users/{id}."""

    classes: list[ClassBrief]


# --- admin: classes (§5.2) --------------------------------------------------


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=2000)


class ClassUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class ClassOut(OutModel):
    """GET /admin/classes (list items), GET /teacher/classes, POST/PATCH /admin/classes."""

    id: int
    name: str
    description: str
    created_at: str
    teacher_count: int
    student_count: int


class AssignmentBrief(OutModel):
    id: int
    title: str
    due_at: str | None
    created_at: str


class ClassDetailOut(ClassOut):
    """GET /admin/classes/{id}."""

    teachers: list[UserOut]
    students: list[UserOut]
    assignments: list[AssignmentBrief]


class MembersAdd(BaseModel):
    user_ids: list[int] = Field(min_length=1, max_length=500)


class EmptyIn(BaseModel):
    """Body `{}` (POST /admin/assignments/{id}/summary). Extra fields are ignored."""


# --- jobs (§6.2) -------------------------------------------------------------


class JobOut(OutModel):
    id: int
    kind: JobKind
    status: JobStatus
    result: dict[str, Any] | None
    error: str | None
    created_at: str
    finished_at: str | None


class JobNewOut(BaseModel):
    created: bool
    job: JobOut


class JobCheckOut(BaseModel):
    job: JobOut | None


# --- teacher: questions (§5.3) ----------------------------------------------


class FloatTolerance(OutModel):
    abs: float = Field(default=0, ge=0, le=1)
    rel: float = Field(default=0, ge=0, le=1)

    @model_validator(mode="after")
    def _one_positive(self) -> "FloatTolerance":
        if self.abs == 0 and self.rel == 0:
            raise ValueError("at least one of abs / rel must be > 0")
        return self


class TestCaseIn(BaseModel):
    __test__ = False

    stdin: str = ""
    expected_stdout: str
    is_hidden: bool

    @field_validator("stdin", "expected_stdout")
    @classmethod
    def _size(cls, value: str) -> str:
        return _check_bytes(value, MAX_IO_BYTES)


class QuestionIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    statement_md: str = Field(min_length=1, max_length=20_000)
    difficulty: Difficulty
    topics: list[str] = Field(default_factory=list)
    time_limit_ms: int = Field(default=2000, ge=100, le=10_000)
    memory_limit_mb: int = Field(default=256, ge=16, le=1024)
    float_tolerance: FloatTolerance | None = None
    test_cases: list[TestCaseIn] = Field(min_length=2, max_length=50)

    @field_validator("topics")
    @classmethod
    def _topics(cls, value: list[str]) -> list[str]:
        topics = _normalize_topics(value)
        if len(topics) > 5:
            raise ValueError("at most 5 topics")
        return topics

    @model_validator(mode="after")
    def _visible_and_hidden(self) -> "QuestionIn":
        if not any(not t.is_hidden for t in self.test_cases):
            raise ValueError("at least one visible test case is required")
        if not any(t.is_hidden for t in self.test_cases):
            raise ValueError("at least one hidden test case is required")
        return self


class TestCaseOut(OutModel):
    __test__ = False

    position: int
    stdin: str
    expected_stdout: str
    is_hidden: bool


class QuestionSummaryOut(OutModel):
    """GET /teacher/questions list items (no test-case bodies)."""

    id: int
    title: str
    difficulty: Difficulty
    topics: list[str]
    time_limit_ms: int
    memory_limit_mb: int
    float_tolerance: FloatTolerance | None
    source_job_id: int | None
    created_at: str
    updated_at: str


class QuestionOut(QuestionSummaryOut):
    """GET/POST/PUT /teacher/questions/{id}, approve → 201."""

    statement_md: str
    test_cases: list[TestCaseOut]


# --- teacher: question generation (§7.2) ------------------------------------


class QuestionGenIn(BaseModel):
    difficulty: Difficulty
    topics: list[str] = Field(min_length=1, max_length=5)
    prompt: str = Field(min_length=1, max_length=2000)
    parent_job_id: int | None = None
    feedback: str | None = Field(default=None, max_length=2000)

    @field_validator("topics")
    @classmethod
    def _topics(cls, value: list[str]) -> list[str]:
        return _normalize_topics(value)

    @model_validator(mode="after")
    def _feedback_with_parent(self) -> "QuestionGenIn":
        if self.parent_job_id is not None and not (self.feedback and self.feedback.strip()):
            raise ValueError("feedback is required with parent_job_id")
        return self


class QuestionDraft(QuestionIn):
    """The validated LLM draft (job result `{"draft": ...}`). Unknown fields are dropped.
    Build it from the LLM JSON plus the request's difficulty/topics; approve with
    `QuestionIn.model_validate(draft.model_dump(exclude={"reference_solution"}))`."""

    reference_solution: str = Field(min_length=1)

    @field_validator("reference_solution")
    @classmethod
    def _solution(cls, value: str) -> str:
        return _check_code(value)


class QuestionGenResult(BaseModel):
    draft: QuestionDraft


# --- teacher: assignments (§5.3) --------------------------------------------


def _distinct_ids(ids: list[int]) -> list[int]:
    if len(set(ids)) != len(ids):
        raise ValueError("question_ids must be distinct")
    return ids


class AssignmentCreate(BaseModel):
    class_id: int
    title: str = Field(min_length=1, max_length=200)
    description_md: str = Field(default="", max_length=5000)
    due_at: datetime | None = None  # naive values are treated as UTC
    question_ids: list[int] = Field(min_length=1, max_length=3)

    @field_validator("question_ids")
    @classmethod
    def _distinct(cls, value: list[int]) -> list[int]:
        return _distinct_ids(value)


class AssignmentUpdate(BaseModel):
    """PATCH: use `body.model_dump(exclude_unset=True)`; `due_at: null` clears the deadline."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description_md: str | None = Field(default=None, max_length=5000)
    due_at: datetime | None = None
    question_ids: list[int] | None = Field(default=None, min_length=1, max_length=3)

    @field_validator("question_ids")
    @classmethod
    def _distinct(cls, value: list[int] | None) -> list[int] | None:
        return None if value is None else _distinct_ids(value)


class AssignmentQuestionOut(OutModel):
    id: int
    position: int
    title: str
    difficulty: Difficulty


class AssignmentOut(OutModel):
    """Teacher assignment list items and detail."""

    id: int
    class_id: int
    class_name: str
    created_by: int | None
    title: str
    description_md: str
    due_at: str | None
    created_at: str
    updated_at: str
    questions: list[AssignmentQuestionOut]


# --- student (§5.4) ---------------------------------------------------------


class StudentQuestionBrief(BaseModel):
    id: int
    position: int
    title: str
    difficulty: Difficulty
    solved: bool


class StudentAssignmentOut(BaseModel):
    """GET /student/assignments (list items) and /student/assignments/{aid}."""

    id: int
    class_id: int
    class_name: str
    title: str
    description_md: str
    due_at: str | None
    questions: list[StudentQuestionBrief]


class VisibleTestCase(OutModel):
    position: int
    stdin: str
    expected_stdout: str


class StudentQuestionOut(BaseModel):
    """GET /student/assignments/{aid}/questions/{qid}: visible tests only."""

    id: int
    title: str
    statement_md: str
    difficulty: Difficulty
    topics: list[str]
    time_limit_ms: int
    memory_limit_mb: int
    float_tolerance: FloatTolerance | None
    test_cases: list[VisibleTestCase]
    solved: bool


class CodeIn(BaseModel):
    """Body of run / submit / hint: 1 B - 64 KiB, no NUL bytes."""

    code: str = Field(min_length=1)

    @field_validator("code")
    @classmethod
    def _code(cls, value: str) -> str:
        return _check_code(value)


class SubmissionBriefOut(OutModel):
    id: int
    verdict: Verdict
    passed: int
    total: int
    created_at: str


class SubmissionOut(SubmissionBriefOut):
    code: str


# --- job results (§7) -------------------------------------------------------


class JudgeTestResult(BaseModel):
    index: int
    hidden: bool
    status: Verdict
    time_ms: int
    memory_kb: int | None
    stdout_preview: str | None = None  # never set for hidden tests
    stderr_preview: str | None = None  # never set for hidden tests

    @model_serializer(mode="wrap")
    def _drop_empty_previews(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data = handler(self)
        for key in ("stdout_preview", "stderr_preview"):
            if data.get(key) is None:
                data.pop(key, None)
        return data


class JudgeResult(BaseModel):
    """Result of run / submit jobs (§7.4). `model_dump()` omits empty previews per test."""

    verdict: Verdict
    passed: int
    total: int
    failed_test_index: int | None
    error_message: str | None
    max_time_ms: int
    max_memory_kb: int | None
    results: list[JudgeTestResult]


class HintResult(BaseModel):
    hint_md: str
    tools_used: list[str]


class SummaryResult(BaseModel):
    stats: dict[str, Any]
    summary_md: str
