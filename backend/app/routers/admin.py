import functools

from fastapi import APIRouter, Depends, HTTPException, Response

from app.ai import summary
from app.auth import hash_password, require_admin
from app.config import AppContext, get_ctx
from app.jobs.runner import check_job_response, latest_job, new_job_response, start_job
from app.repos import Conflict
from app.repos import assignments as assignments_repo
from app.repos import classes as classes_repo
from app.repos import users as users_repo
from app.repos.users import User
from app.schemas import (
    AssignmentBrief,
    ClassBrief,
    ClassCreate,
    ClassDetailOut,
    ClassOut,
    ClassUpdate,
    EmptyIn,
    JobCheckOut,
    MembersAdd,
    Role,
    UserCreate,
    UserDetailOut,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _conflict(e: Conflict) -> HTTPException:
    return HTTPException(status_code=409, detail=str(e) or "conflict")


# --- users ---------------------------------------------------------------------


@router.get("/users")
async def list_users(role: Role | None = None, ctx: AppContext = Depends(get_ctx)) -> list[UserOut]:
    return [UserOut.model_validate(u) for u in await users_repo.list_users(ctx.db, role)]


@router.post("/users", status_code=201)
async def create_user(body: UserCreate, ctx: AppContext = Depends(get_ctx)) -> UserOut:
    try:
        user = await users_repo.create(
            ctx.db, body.username, body.display_name, await hash_password(body.password), body.role
        )
    except Conflict as e:
        raise _conflict(e) from e
    return UserOut.model_validate(user)


@router.get("/users/{user_id}")
async def get_user(user_id: int, ctx: AppContext = Depends(get_ctx)) -> UserDetailOut:
    user = await users_repo.get(ctx.db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    classes = await classes_repo.list_for_user(ctx.db, user_id)
    return UserDetailOut(
        **UserOut.model_validate(user).model_dump(),
        classes=[ClassBrief(id=c.id, name=c.name) for c in classes],
    )


@router.patch("/users/{user_id}")
async def update_user(user_id: int, body: UserUpdate, ctx: AppContext = Depends(get_ctx)) -> UserOut:
    fields = body.model_dump(exclude_unset=True)
    if "password" in fields:
        fields["password_hash"] = await hash_password(fields.pop("password"))
    try:
        user = await users_repo.update(ctx.db, user_id, **fields)
    except Conflict as e:
        raise _conflict(e) from e
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return UserOut.model_validate(user)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int, admin: User = Depends(require_admin), ctx: AppContext = Depends(get_ctx)
) -> Response:
    target = await users_repo.get(ctx.db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="user not found")
    if target.id == admin.id:
        raise HTTPException(status_code=409, detail="You cannot delete yourself.")
    if target.role == "admin" and await users_repo.count_admins(ctx.db) <= 1:
        raise HTTPException(status_code=409, detail="The last admin cannot be deleted.")
    await users_repo.delete(ctx.db, user_id)
    return Response(status_code=204)


# --- classes -------------------------------------------------------------------


async def _class_detail(ctx: AppContext, class_id: int) -> ClassDetailOut:
    row = await classes_repo.get(ctx.db, class_id)
    if row is None:
        raise HTTPException(status_code=404, detail="class not found")
    members = await classes_repo.members(ctx.db, class_id)
    assignments = await assignments_repo.list_for_class(ctx.db, class_id)
    return ClassDetailOut(
        **ClassOut.model_validate(row).model_dump(),
        teachers=[UserOut.model_validate(u) for u in members if u.role == "teacher"],
        students=[UserOut.model_validate(u) for u in members if u.role == "student"],
        assignments=[
            AssignmentBrief(id=a.id, title=a.title, due_at=a.due_at, created_at=a.created_at) for a in assignments
        ],
    )


@router.get("/classes")
async def list_classes(ctx: AppContext = Depends(get_ctx)) -> list[ClassOut]:
    return [ClassOut.model_validate(c) for c in await classes_repo.list_classes(ctx.db)]


@router.post("/classes", status_code=201)
async def create_class(body: ClassCreate, ctx: AppContext = Depends(get_ctx)) -> ClassOut:
    try:
        row = await classes_repo.create(ctx.db, body.name, body.description)
    except Conflict as e:
        raise _conflict(e) from e
    return ClassOut.model_validate(row)


@router.get("/classes/{class_id}")
async def get_class(class_id: int, ctx: AppContext = Depends(get_ctx)) -> ClassDetailOut:
    return await _class_detail(ctx, class_id)


@router.patch("/classes/{class_id}")
async def update_class(class_id: int, body: ClassUpdate, ctx: AppContext = Depends(get_ctx)) -> ClassOut:
    try:
        row = await classes_repo.update(ctx.db, class_id, **body.model_dump(exclude_unset=True))
    except Conflict as e:
        raise _conflict(e) from e
    if row is None:
        raise HTTPException(status_code=404, detail="class not found")
    return ClassOut.model_validate(row)


@router.delete("/classes/{class_id}", status_code=204)
async def delete_class(class_id: int, ctx: AppContext = Depends(get_ctx)) -> Response:
    if not await classes_repo.delete(ctx.db, class_id):
        raise HTTPException(status_code=404, detail="class not found")
    return Response(status_code=204)


@router.post("/classes/{class_id}/members")
async def add_members(class_id: int, body: MembersAdd, ctx: AppContext = Depends(get_ctx)) -> ClassDetailOut:
    if await classes_repo.get(ctx.db, class_id) is None:
        raise HTTPException(status_code=404, detail="class not found")
    ids = list(dict.fromkeys(body.user_ids))
    found = {u.id: u for u in await users_repo.get_many(ctx.db, ids)}
    if len(found) != len(ids):
        raise HTTPException(status_code=422, detail="Some users do not exist.")
    if any(u.role == "admin" for u in found.values()):
        raise HTTPException(status_code=422, detail="Admins cannot be class members.")
    await classes_repo.add_members(ctx.db, class_id, ids)
    return await _class_detail(ctx, class_id)


@router.delete("/classes/{class_id}/members/{user_id}", status_code=204)
async def remove_member(class_id: int, user_id: int, ctx: AppContext = Depends(get_ctx)) -> Response:
    if not await classes_repo.remove_member(ctx.db, class_id, user_id):
        raise HTTPException(status_code=404, detail="membership not found")
    return Response(status_code=204)


# --- assignment summary (§7.3) ---------------------------------------------------


@router.post("/assignments/{assignment_id}/summary")
async def new_summary(
    assignment_id: int,
    body: EmptyIn | None = None,
    admin: User = Depends(require_admin),
    ctx: AppContext = Depends(get_ctx),
):
    if await assignments_repo.get(ctx.db, assignment_id) is None:
        raise HTTPException(status_code=404, detail="assignment not found")
    job, created = await start_job(
        ctx.db,
        admin.id,
        "assignment_summary",
        f"a{assignment_id}",
        {"assignment_id": assignment_id},
        functools.partial(summary.run_summary, ctx),
        ctx.settings.llm_job_timeout_s,
    )
    return new_job_response(job, created)


@router.get("/assignments/{assignment_id}/summary")
async def check_summary(
    assignment_id: int, admin: User = Depends(require_admin), ctx: AppContext = Depends(get_ctx)
) -> JobCheckOut:
    return check_job_response(await latest_job(ctx.db, admin.id, "assignment_summary", f"a{assignment_id}"))
