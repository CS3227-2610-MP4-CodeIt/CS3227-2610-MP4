from fastapi import APIRouter, Depends, HTTPException, Response

from app.auth import create_session, current_token_hash, current_user, verify_dummy, verify_password
from app.config import AppContext, get_ctx
from app.repos import users as users_repo
from app.repos.users import User
from app.schemas import LoginIn, LoginOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginIn, ctx: AppContext = Depends(get_ctx)) -> LoginOut:
    found = await users_repo.get_with_password_hash(ctx.db, body.username)
    if found is None:
        await verify_dummy(body.password)
        raise HTTPException(status_code=401, detail="invalid credentials")
    user, password_hash = found
    if not await verify_password(password_hash, body.password):
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = await create_session(ctx.db, user.id, ctx.settings.session_ttl_hours)
    return LoginOut(token=token, user=UserOut.model_validate(user))


@router.post("/logout", status_code=204, dependencies=[Depends(current_user)])
async def logout(token_hash: str = Depends(current_token_hash), ctx: AppContext = Depends(get_ctx)) -> Response:
    await users_repo.delete_session(ctx.db, token_hash)
    return Response(status_code=204)


@router.get("/me")
async def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut.model_validate(user)
