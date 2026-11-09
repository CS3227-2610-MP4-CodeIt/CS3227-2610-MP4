import re

from fastapi import APIRouter, Depends, HTTPException

from app.auth import current_user
from app.config import AppContext, get_ctx
from app.jobs.runner import job_out
from app.repos import jobs as jobs_repo
from app.repos.users import User
from app.schemas import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
async def get_job(
    job_id: int, user: User = Depends(current_user), ctx: AppContext = Depends(get_ctx)
) -> JobOut:
    job = await jobs_repo.get(ctx.db, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="job not found")
    if job.kind == "complexity":
        from app.routers.student import _complexity_submission

        match = re.fullmatch(r"a(\d+):q(\d+):s(\d+)", job.target_key)
        if user.role != "student" or match is None:
            raise HTTPException(status_code=404, detail="job not found")
        await _complexity_submission(ctx, user, *(int(value) for value in match.groups()))
    return job_out(job)
