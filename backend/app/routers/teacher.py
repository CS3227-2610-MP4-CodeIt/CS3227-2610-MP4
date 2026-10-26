from functools import partial

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from app.ai import guards, question_gen
from app.auth import require_teacher
from app.config import AppContext, get_ctx
from app.jobs.runner import check_job_response, latest_job, new_job_response, start_job
from app.repos import Conflict
from app.repos import assignments as assignments_repo
from app.repos import classes as classes_repo
from app.repos import jobs as jobs_repo
from app.repos import questions as questions_repo
from app.repos.users import User
from app.schemas import (
    AssignmentCreate,
    AssignmentOut,
    AssignmentUpdate,
    ClassOut,
    JobCheckOut,
    QuestionDraft,
    QuestionGenIn,
    QuestionGenResult,
    QuestionIn,
    QuestionOut,
    QuestionSummaryOut,
)

router = APIRouter(prefix="/teacher", tags=["teacher"], dependencies=[Depends(require_teacher)])

KIND = "question_gen"


async def _own_question(ctx: AppContext, user: User, question_id: int):
    question = await questions_repo.get(ctx.db, question_id)
    if question is None or question.created_by != user.id:
        raise HTTPException(status_code=404, detail="question not found")
    return question


async def _check_question_ids(ctx: AppContext, user: User, question_ids: list[int]) -> None:
    for qid in question_ids:
        await _own_question(ctx, user, qid)


async def _own_assignment(ctx: AppContext, user: User, assignment_id: int):
    assignment = await assignments_repo.get(ctx.db, assignment_id)
    if assignment is None or not await classes_repo.is_member(ctx.db, assignment.class_id, user.id):
        raise HTTPException(status_code=404, detail="assignment not found")
    return assignment


async def _created_assignment(ctx: AppContext, user: User, assignment_id: int):
    assignment = await _own_assignment(ctx, user, assignment_id)
    if assignment.created_by != user.id:
        raise HTTPException(status_code=404, detail="assignment not found")
    return assignment


async def _own_gen_job(ctx: AppContext, user: User, job_id: int):
    job = await jobs_repo.get(ctx.db, job_id)
    if job is None or job.user_id != user.id or job.kind != KIND:
        raise HTTPException(status_code=404, detail="job not found")
    return job


# --- classes ---------------------------------------------------------------


@router.get("/classes")
async def list_classes(user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)) -> list[ClassOut]:
    return [ClassOut.model_validate(c) for c in await classes_repo.list_for_user(ctx.db, user.id)]


# --- questions -------------------------------------------------------------


@router.get("/questions")
async def list_questions(
    user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)
) -> list[QuestionSummaryOut]:
    return [QuestionSummaryOut.model_validate(q) for q in await questions_repo.list_by_owner(ctx.db, user.id)]


@router.post("/questions", status_code=201)
async def create_question(
    body: QuestionIn, user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)
) -> QuestionOut:
    return QuestionOut.model_validate(await questions_repo.create(ctx.db, user.id, body))


@router.get("/questions/{question_id}")
async def get_question(
    question_id: int, user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)
) -> QuestionOut:
    return QuestionOut.model_validate(await _own_question(ctx, user, question_id))


@router.put("/questions/{question_id}")
async def replace_question(
    question_id: int, body: QuestionIn, user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)
) -> QuestionOut:
    await _own_question(ctx, user, question_id)
    question = await questions_repo.replace(ctx.db, question_id, body)
    if question is None:
        raise HTTPException(status_code=404, detail="question not found")
    return QuestionOut.model_validate(question)


@router.delete("/questions/{question_id}", status_code=204)
async def delete_question(
    question_id: int, user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)
) -> Response:
    await _own_question(ctx, user, question_id)
    try:
        await questions_repo.delete(ctx.db, question_id)
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return Response(status_code=204)


# --- question generation ---------------------------------------------------


@router.post("/question-generations")
async def new_generation(
    body: QuestionGenIn, user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)
) -> JSONResponse:
    guards.reject_injection(body.prompt, body.feedback, *body.topics)
    job_input = body.model_dump(mode="json", exclude={"parent_job_id"})
    job_input["parent_draft"] = None
    if body.parent_job_id is not None:
        parent = await _own_gen_job(ctx, user, body.parent_job_id)
        if parent.status != "success" or not parent.result:
            raise HTTPException(status_code=404, detail="job not found")
        job_input["parent_draft"] = parent.result["draft"]
    handler = partial(question_gen.run_question_gen, ctx)
    job, created = await start_job(ctx.db, user.id, KIND, "-", job_input, handler, ctx.settings.llm_job_timeout_s)
    return new_job_response(job, created)


@router.get("/question-generations")
async def check_generation(user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)) -> JobCheckOut:
    return check_job_response(await latest_job(ctx.db, user.id, KIND, "-"))


@router.post("/question-generations/{job_id}/approve", status_code=201)
async def approve_generation(
    job_id: int, user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)
) -> QuestionOut:
    job = await _own_gen_job(ctx, user, job_id)
    if job.status != "success" or not job.result:
        raise HTTPException(status_code=409, detail="this job has no draft to approve")
    draft: QuestionDraft = QuestionGenResult.model_validate(job.result).draft
    data = QuestionIn.model_validate(draft.model_dump(exclude={"reference_solution"}))
    try:
        question = await questions_repo.create(ctx.db, user.id, data, source_job_id=job.id)
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return QuestionOut.model_validate(question)


# --- assignments -----------------------------------------------------------


@router.get("/assignments")
async def list_assignments(
    class_id: int | None = Query(default=None),
    user: User = Depends(require_teacher),
    ctx: AppContext = Depends(get_ctx),
) -> list[AssignmentOut]:
    items = await assignments_repo.list_for_member(ctx.db, user.id, class_id)
    return [AssignmentOut.model_validate(a) for a in items]


@router.post("/assignments", status_code=201)
async def create_assignment(
    body: AssignmentCreate, user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)
) -> AssignmentOut:
    if not await classes_repo.is_member(ctx.db, body.class_id, user.id):
        raise HTTPException(status_code=404, detail="class not found")
    await _check_question_ids(ctx, user, body.question_ids)
    assignment = await assignments_repo.create(
        ctx.db, body.class_id, user.id, body.title, body.description_md, body.due_at, body.question_ids
    )
    return AssignmentOut.model_validate(assignment)


@router.get("/assignments/{assignment_id}")
async def get_assignment(
    assignment_id: int, user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)
) -> AssignmentOut:
    return AssignmentOut.model_validate(await _own_assignment(ctx, user, assignment_id))


@router.get("/assignments/{assignment_id}/questions/{question_id}")
async def get_assignment_question(
    assignment_id: int, question_id: int, user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)
) -> QuestionOut:
    """Read-only view for any teacher of the class, including co-teachers who did not write it."""
    assignment = await _own_assignment(ctx, user, assignment_id)
    question = await questions_repo.get(ctx.db, question_id) if assignment.has_question(question_id) else None
    if question is None:
        raise HTTPException(status_code=404, detail="question not found")
    return QuestionOut.model_validate(question)


@router.patch("/assignments/{assignment_id}")
async def update_assignment(
    assignment_id: int,
    body: AssignmentUpdate,
    user: User = Depends(require_teacher),
    ctx: AppContext = Depends(get_ctx),
) -> AssignmentOut:
    await _created_assignment(ctx, user, assignment_id)
    changes = body.model_dump(exclude_unset=True)
    if changes.get("title", "") is None or changes.get("description_md", "") is None:
        raise HTTPException(status_code=422, detail="title and description_md cannot be null")
    if changes.get("question_ids", [1]) is None:
        raise HTTPException(status_code=422, detail="question_ids cannot be null")
    if "question_ids" in changes:
        await _check_question_ids(ctx, user, changes["question_ids"])
    try:
        assignment = await assignments_repo.update(ctx.db, assignment_id, **changes)
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    if assignment is None:
        raise HTTPException(status_code=404, detail="assignment not found")
    return AssignmentOut.model_validate(assignment)


@router.delete("/assignments/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: int, user: User = Depends(require_teacher), ctx: AppContext = Depends(get_ctx)
) -> Response:
    await _created_assignment(ctx, user, assignment_id)
    await assignments_repo.delete(ctx.db, assignment_id)
    return Response(status_code=204)
