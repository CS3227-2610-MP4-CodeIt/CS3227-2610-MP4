from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from fastapi import Request
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from app.clients.executor import ExecutorClient
    from app.clients.llm import LLMClient
    from app.db import Database


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["dev", "prod"] = "dev"
    database_path: str = "/data/app.db"
    session_ttl_hours: float = 12
    bootstrap_admin_username: str | None = None
    bootstrap_admin_password: str | None = None
    soclaas_base_url: str
    soclaas_api_key: str
    llm_model: str = "coder"
    llm_job_timeout_s: float = 300
    code_execution_server: str
    executor_token: str


class AppEnv(BaseSettings):
    """Only APP_ENV, needed when the app object is built (before the lifespan reads full Settings)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["dev", "prod"] = "dev"


@dataclass
class AppContext:
    """Everything a router or job handler needs. One per app, stored in app.state.ctx."""

    settings: Settings
    db: "Database"
    llm: "LLMClient"
    executor: "ExecutorClient"


def get_ctx(request: Request) -> AppContext:
    """FastAPI dependency: `ctx: AppContext = Depends(get_ctx)`."""
    return request.app.state.ctx
