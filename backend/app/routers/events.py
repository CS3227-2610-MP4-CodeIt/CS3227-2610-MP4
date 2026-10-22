"""GET /api/events: SSE stream of job notifications for the caller only (spec §6.6)."""

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.auth import current_token_hash, current_user
from app.config import AppContext, get_ctx
from app.db import Database
from app.jobs import events
from app.repos import users as users_repo
from app.repos.users import User

router = APIRouter(tags=["events"])

PING_INTERVAL_S = 15.0  # tests lower this


def _event(name: str, data: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(data)}\n\n"


async def _stream(db: Database, user_id: int, token_hash: str) -> AsyncIterator[str]:
    queue = events.subscribe(user_id)
    try:
        yield _event("ready", {})
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=PING_INTERVAL_S)
            except TimeoutError:
                yield ": ping\n\n"
                session_user = await users_repo.get_session_user(db, token_hash)
                if session_user is None or session_user.id != user_id:
                    return
                continue
            if item is None:  # server shutdown
                return
            yield _event("job", item)
    finally:
        events.unsubscribe(user_id, queue)


@router.get("/events")
async def stream_events(
    user: User = Depends(current_user),
    token_hash: str = Depends(current_token_hash),
    ctx: AppContext = Depends(get_ctx),
) -> StreamingResponse:
    return StreamingResponse(
        _stream(ctx.db, user.id, token_hash),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
