import functools
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app import judging
from app.ai import guards, hints
from app.auth import require_student
from app.clients import executor
from app.config import AppContext, get_ctx
from app.jobs.runner import check_job_response, latest_job, new_job_response, start_job
from app.repos import questions as questions_repo
from app.repos import submissions as submissions_repo
from app.repos.assignments import Assignment
from app.repos import assignments as assignments_repo
from app.repos.users import User
from app.schemas import (
    CodeIn,
    JobCheckOut,
    StudentAssignmentOut,
    StudentQuestionBrief,
    StudentQuestionOut,
    SubmissionBriefOut,
    SubmissionOut,
    VisibleTestCase,
)

router = APIRouter(prefix="/student", tags=["student"], dependencies=[Depends(require_student)])

DUE_MESSAGE = "This assignment is past its due date."


def _assignment_out(a: Assignment, solved: set[tuple[int, int]]) -> StudentAssignmentOut:
    return StudentAssignmentOut(
        id=a.id, class_id=a.class_id, class_name=a.class_name, title=a.title,
        description_md=a.description_md, due_at=a.due_at,
        questions=[
            StudentQuestionBrief(
                id=q.id, position=q.position, title=q.title, difficulty=q.difficulty, solved=(a.id, q.id) in solved
            )
            for q in a.questions
        ],
    )


async def _get_assignment(ctx: AppContext, user: User, aid: int, qid: int | None = None) -> Assignment:
    a = await assignments_repo.get_for_member(ctx.db, aid, user.id)
    if a is None or (qid is not None and not a.has_question(qid)):
        raise HTTPException(status_code=404, detail="Not found")
    return a


@router.get("/assignments", response_model=list[StudentAssignmentOut])
async def list_assignments(user: User = Depends(require_student), ctx: AppContext = Depends(get_ctx)) -> list[StudentAssignmentOut]:
    solved = await submissions_repo.solved_pairs(ctx.db, user.id)
    return [_assignment_out(a, solved) for a in await assignments_repo.list_for_member(ctx.db, user.id)]


@router.get("/assignments/{aid}", response_model=StudentAssignmentOut)
async def get_assignment(aid: int, user: User = Depends(require_student), ctx: AppContext = Depends(get_ctx)) -> StudentAssignmentOut:
    a = await _get_assignment(ctx, user, aid)
    return _assignment_out(a, await submissions_repo.solved_pairs(ctx.db, user.id))


@router.get("/assignments/{aid}/questions/{qid}", response_model=StudentQuestionOut)
async def get_question(aid: int, qid: int, user: User = Depends(require_student), ctx: AppContext = Depends(get_ctx)) -> StudentQuestionOut:
    await _get_assignment(ctx, user, aid, qid)
    q = await questions_repo.get(ctx.db, qid)
    if q is None:
        raise HTTPException(status_code=404, detail="Not found")
    solved = await submissions_repo.solved_pairs(ctx.db, user.id)
    return StudentQuestionOut(
        id=q.id, title=q.title, statement_md=q.statement_md, difficulty=q.difficulty, topics=q.topics,
        time_limit_ms=q.time_limit_ms, memory_limit_mb=q.memory_limit_mb, float_tolerance=q.float_tolerance,
        test_cases=[
            VisibleTestCase(position=t.position, stdin=t.stdin, expected_stdout=t.expected_stdout)
            for t in q.test_cases if not t.is_hidden
        ],
        solved=(aid, qid) in solved,
    )


async def _start_judge(
    kind: str, aid: int, qid: int, body: CodeIn, user: User, ctx: AppContext
):
    a = await _get_assignment(ctx, user, aid, qid)
    if kind == "submit" and a.is_past_due():
        raise HTTPException(status_code=409, detail=DUE_MESSAGE)
    q = await questions_repo.get(ctx.db, qid, with_tests=False)
    if q is None:
        raise HTTPException(status_code=404, detail="Not found")
    n_tests = await questions_repo.count_test_cases(ctx.db, qid, None if kind == "submit" else False)
    job_input: dict[str, Any] = {
        "student_id": user.id, "assignment_id": aid, "question_id": qid, "code": body.code, "submit": kind == "submit",
    }
    job, created = await start_job(
        ctx.db, user.id, kind, f"a{aid}:q{qid}", job_input,
        functools.partial(judging.run_judge, ctx), executor.job_timeout_s(n_tests, q.time_limit_ms),
    )
    return new_job_response(job, created)


@router.post("/assignments/{aid}/questions/{qid}/run")
async def run_code(aid: int, qid: int, body: CodeIn, user: User = Depends(require_student), ctx: AppContext = Depends(get_ctx)):
    return await _start_judge("run", aid, qid, body, user, ctx)


@router.get("/assignments/{aid}/questions/{qid}/run", response_model=JobCheckOut)
async def check_run(aid: int, qid: int, user: User = Depends(require_student), ctx: AppContext = Depends(get_ctx)) -> JobCheckOut:
    await _get_assignment(ctx, user, aid, qid)
    return check_job_response(await latest_job(ctx.db, user.id, "run", f"a{aid}:q{qid}"))


@router.post("/assignments/{aid}/questions/{qid}/submit")
async def submit_code(aid: int, qid: int, body: CodeIn, user: User = Depends(require_student), ctx: AppContext = Depends(get_ctx)):
    return await _start_judge("submit", aid, qid, body, user, ctx)


@router.get("/assignments/{aid}/questions/{qid}/submit", response_model=JobCheckOut)
async def check_submit(aid: int, qid: int, user: User = Depends(require_student), ctx: AppContext = Depends(get_ctx)) -> JobCheckOut:
    await _get_assignment(ctx, user, aid, qid)
    return check_job_response(await latest_job(ctx.db, user.id, "submit", f"a{aid}:q{qid}"))


@router.get("/assignments/{aid}/questions/{qid}/submissions", response_model=list[SubmissionBriefOut])
async def list_submissions(aid: int, qid: int, user: User = Depends(require_student), ctx: AppContext = Depends(get_ctx)) -> list[SubmissionBriefOut]:
    await _get_assignment(ctx, user, aid, qid)
    return [SubmissionBriefOut.model_validate(s) for s in await submissions_repo.list_for(ctx.db, user.id, aid, qid)]


@router.get("/assignments/{aid}/questions/{qid}/submissions/{sid}", response_model=SubmissionOut)
async def get_submission(aid: int, qid: int, sid: int, user: User = Depends(require_student), ctx: AppContext = Depends(get_ctx)) -> SubmissionOut:
    await _get_assignment(ctx, user, aid, qid)
    s = await submissions_repo.get(ctx.db, sid)
    if s is None or s.user_id != user.id or s.assignment_id != aid or s.question_id != qid:
        raise HTTPException(status_code=404, detail="Not found")
    return SubmissionOut.model_validate(s)


@router.post("/assignments/{aid}/questions/{qid}/hint")
async def request_hint(aid: int, qid: int, body: CodeIn, user: User = Depends(require_student), ctx: AppContext = Depends(get_ctx)):
    await _get_assignment(ctx, user, aid, qid)
    guards.reject_injection(body.code)
    job_input = {"student_id": user.id, "assignment_id": aid, "question_id": qid, "code": body.code}
    job, created = await start_job(
        ctx.db, user.id, "hint", f"a{aid}:q{qid}", job_input,
        functools.partial(hints.run_hint, ctx), ctx.settings.llm_job_timeout_s,
    )
    return new_job_response(job, created)


@router.get("/assignments/{aid}/questions/{qid}/hint", response_model=JobCheckOut)
async def check_hint(aid: int, qid: int, user: User = Depends(require_student), ctx: AppContext = Depends(get_ctx)) -> JobCheckOut:
    await _get_assignment(ctx, user, aid, qid)
    return check_job_response(await latest_job(ctx.db, user.id, "hint", f"a{aid}:q{qid}"))
