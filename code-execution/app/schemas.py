from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, SerializerFunctionWrapHandler, field_validator, model_serializer, model_validator

MAX_CODE_BYTES = 64 * 1024
MAX_IO_BYTES = 1024 * 1024


def _check_size(value: str, limit: int) -> str:
    if len(value.encode()) > limit:
        raise ValueError(f"must be at most {limit} bytes")
    return value


class FloatTolerance(BaseModel):
    abs: float = Field(default=0, ge=0, le=1)
    rel: float = Field(default=0, ge=0, le=1)

    @model_validator(mode="after")
    def _one_positive(self) -> "FloatTolerance":
        if self.abs == 0 and self.rel == 0:
            raise ValueError("at least one of abs / rel must be > 0")
        return self


class TestCase(BaseModel):
    __test__ = False  # not a pytest test class

    stdin: str = ""
    expected_stdout: str

    @field_validator("stdin", "expected_stdout")
    @classmethod
    def _size(cls, value: str) -> str:
        return _check_size(value, MAX_IO_BYTES)


class ExecuteRequest(BaseModel):
    code: str = Field(min_length=1)
    time_limit_ms: int = Field(ge=100, le=10_000)
    memory_limit_mb: int = Field(ge=16, le=1024)
    float_tolerance: FloatTolerance | None = None
    test_cases: list[TestCase] = Field(min_length=1, max_length=100)

    @field_validator("code")
    @classmethod
    def _code(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("must not contain NUL bytes")
        return _check_size(value, MAX_CODE_BYTES)


class Verdict(StrEnum):
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    RUNTIME_ERROR = "RUNTIME_ERROR"


class TestResult(BaseModel):
    __test__ = False  # not a pytest test class

    index: int
    status: Verdict
    time_ms: int
    memory_kb: int | None
    stdout_preview: str | None = None
    stderr_preview: str | None = None

    @model_serializer(mode="wrap")
    def _drop_empty_previews(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data = handler(self)
        for key in ("stdout_preview", "stderr_preview"):
            if data.get(key) is None:
                data.pop(key, None)
        return data


class ExecuteResponse(BaseModel):
    verdict: Verdict
    passed: int
    total: int
    failed_test_index: int | None
    error_message: str | None
    max_time_ms: int
    max_memory_kb: int | None
    results: list[TestResult]
