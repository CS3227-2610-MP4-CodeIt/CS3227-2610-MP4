"""Password hashing, session tokens and the current_user / require_role dependencies (spec §4)."""

import asyncio
import hashlib
import secrets
from collections.abc import Awaitable, Callable
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import AppContext, get_ctx
from app.db import Database, now_iso
from app.repos import users as users_repo
from app.repos.users import User

_hasher = PasswordHasher()  # argon2id
_bearer = HTTPBearer(auto_error=False)
_DUMMY_HASH = _hasher.hash("dummy password for timing")


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(_hasher.hash, password)


async def verify_password(password_hash: str, password: str) -> bool:
    def verify() -> bool:
        try:
            return _hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            return False

    return await asyncio.to_thread(verify)


async def verify_dummy(password: str) -> None:
    """Spends the same time as a real check, for unknown usernames."""
    await verify_password(_DUMMY_HASH, password)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_session(db: Database, user_id: int, ttl_hours: float) -> str:
    """Creates a session and returns the raw token (only its hash is stored)."""
    token = secrets.token_urlsafe(32)
    await users_repo.create_session(db, token_hash(token), user_id, now_iso(timedelta(hours=ttl_hours)))
    return token


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="not authenticated", headers={"WWW-Authenticate": "Bearer"})


async def current_token_hash(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    """sha256 of the bearer token; 401 if there is no bearer token."""
    if credentials is None or not credentials.credentials:
        raise _unauthorized()
    return token_hash(credentials.credentials)


async def current_user(token_hash_: str = Depends(current_token_hash), ctx: AppContext = Depends(get_ctx)) -> User:
    """The logged-in user; 401 for a missing / unknown / expired token or a deleted user."""
    user = await users_repo.get_session_user(ctx.db, token_hash_)
    if user is None:
        raise _unauthorized()
    return user


def require_role(*roles: str) -> Callable[..., Awaitable[User]]:
    """Dependency factory: 403 unless the user has one of the roles. Prefer the shared instances
    below so FastAPI caches the lookup per request."""

    async def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="forbidden")
        return user

    return dependency


require_admin = require_role("admin")
require_teacher = require_role("teacher")
require_student = require_role("student")
