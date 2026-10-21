import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app import judge
from app.auth import require_token
from app.config import Settings
from app.schemas import ExecuteRequest, ExecuteResponse

MAX_BODY_BYTES = 16 * 1024 * 1024
RETRY_AFTER_S = 5


class BodySizeLimit:
    """Rejects bodies over MAX_BODY_BYTES with 413 before they are parsed."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        length = dict(scope["headers"]).get(b"content-length")
        if length is not None and length.isdigit() and int(length) > MAX_BODY_BYTES:
            await JSONResponse({"detail": "Request body too large"}, status_code=413)(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > MAX_BODY_BYTES:
                    raise HTTPException(status_code=413, detail="Request body too large")
            return message

        await self.app(scope, limited_receive, send)


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        s = settings or Settings()  # type: ignore[call-arg]  # EXECUTOR_TOKEN comes from env
        os.makedirs(s.work_root, exist_ok=True)
        app.state.settings = s
        app.state.job_semaphore = asyncio.Semaphore(s.max_concurrent_jobs)
        yield

    app = FastAPI(title="Code Execution Service", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.add_middleware(BodySizeLimit)

    @app.get("/health")
    async def health(request: Request) -> dict:
        settings: Settings = request.app.state.settings
        semaphore: asyncio.Semaphore = request.app.state.job_semaphore
        return {"status": "ok", "available_slots": semaphore._value, "max_slots": settings.max_concurrent_jobs}

    @app.post("/v1/execute", dependencies=[Depends(require_token)])
    async def execute(body: ExecuteRequest, request: Request) -> ExecuteResponse:
        settings: Settings = request.app.state.settings
        semaphore: asyncio.Semaphore = request.app.state.job_semaphore
        try:
            async with asyncio.timeout(settings.queue_timeout_s):
                await semaphore.acquire()
        except TimeoutError:
            raise HTTPException(
                status_code=503, detail="All execution slots are busy", headers={"Retry-After": str(RETRY_AFTER_S)}
            )
        try:
            return await judge.run_job(body, settings)
        finally:
            semaphore.release()

    return app


app = create_app()
