from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    executor_token: str
    max_concurrent_jobs: int = 100
    queue_timeout_s: float = 30
    work_root: str = "/work"
    wall_grace_s: float = 0.5
    as_overhead_mb: int = 32
    fsize_limit_bytes: int = 1024 * 1024
    max_stdout_bytes: int = 4 * 1024 * 1024
