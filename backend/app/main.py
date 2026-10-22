from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import hash_password
from app.clients.executor import ExecutorClient
from app.clients.llm import LLMClient
from app.config import AppContext, AppEnv, Settings
from app.db import Database
from app.jobs import events, runner
from app.repos import users as users_repo
from app.routers import admin, auth, student, teacher
from app.routers import events as events_router
from app.routers import jobs as jobs_router
from app.schemas import HealthOut
from app.seed import seed_demo


async def bootstrap_admin(db: Database, settings: Settings) -> None:
    """Creates the first admin from env if no admin exists (spec §4)."""
    username, password = settings.bootstrap_admin_username, settings.bootstrap_admin_password
    if not username or not password or await users_repo.count_admins(db) > 0:
        return
    if await users_repo.get_with_password_hash(db, username) is not None:
        raise RuntimeError(f"BOOTSTRAP_ADMIN_USERNAME {username!r} is taken by a non-admin user")
    await users_repo.create(db, username, "Administrator", await hash_password(password), "admin")


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        s = settings or Settings()  # type: ignore[call-arg]  # required values come from env
        if s.app_env == "prod" and not s.code_execution_server.startswith("https://"):
            raise RuntimeError("CODE_EXECUTION_SERVER must be https:// in prod")
        db = Database(s.database_path)
        await db.init_schema()
        await runner.recover(db)
        await bootstrap_admin(db, s)
        if s.app_env == "dev":
            await seed_demo(db)

        llm = LLMClient(s.soclaas_base_url, s.soclaas_api_key, s.llm_model)
        executor = ExecutorClient(s.code_execution_server, s.executor_token)
        try:
            await llm.check_model()
            app.state.ctx = AppContext(settings=s, db=db, llm=llm, executor=executor)
            yield
            await runner.shutdown(db)
            events.close_all()
        finally:
            await llm.aclose()
            await executor.aclose()

    app_env = settings.app_env if settings else AppEnv().app_env
    docs = app_env != "prod"
    app = FastAPI(
        title="Coding Assignments API",
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    @app.get("/api/health", tags=["health"])
    async def health() -> HealthOut:
        return HealthOut()

    for module in (auth, admin, teacher, student, jobs_router, events_router):
        app.include_router(module.router, prefix="/api")
    return app


app = create_app()
