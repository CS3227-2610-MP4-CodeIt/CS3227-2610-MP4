"""SoCLaaS chat-completions client (spec §9.1)."""

import asyncio
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.jobs.runner import UserFacingError

UNAVAILABLE = "The AI service is unavailable. Try again later."
RETRY_STATUSES = (429, 503)
DEFAULT_RETRY_DELAYS_S = (2.0, 5.0)
HTTP_TIMEOUT_S = 300.0


@dataclass
class ChatReply:
    content: str  # trimmed; "" if the model sent none
    tool_calls: list[dict[str, Any]] = field(default_factory=list)  # OpenAI format, as returned
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None

    def assistant_message(self) -> dict[str, Any]:
        """The reply as a message to append to the conversation before the tool results."""
        message: dict[str, Any] = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            message["tool_calls"] = self.tool_calls
        return message


def error_message(response: httpx.Response) -> str:
    """Reads both SoCLaaS error shapes: {"error": "..."} and {"error": {"message": ...}}."""
    try:
        error = response.json().get("error")
    except (ValueError, AttributeError):
        return response.text[:200]
    if isinstance(error, dict):
        return str(error.get("message", ""))
    return str(error or "")


def gateway_origin(base_url: str) -> str:
    """SOCLAAS_BASE_URL is the origin without /v1 (§9.1); a trailing slash or /v1 is tolerated."""
    return base_url.rstrip("/").removesuffix("/v1").rstrip("/")


class LLMClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        retry_delays_s: tuple[float, ...] = DEFAULT_RETRY_DELAYS_S,
    ) -> None:
        self.model = model
        self.retry_delays_s = retry_delays_s
        self._http = httpx.AsyncClient(
            base_url=gateway_origin(base_url),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=HTTP_TIMEOUT_S,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def list_models(self) -> list[str]:
        response = await self._http.get("/v1/models")
        response.raise_for_status()
        return [m["id"] for m in response.json().get("data", [])]

    async def check_model(self) -> None:
        """Startup: fail fast if LLM_MODEL is not available to this key."""
        models = await self.list_models()
        if self.model not in models:
            raise RuntimeError(f"LLM_MODEL {self.model!r} is not in GET /v1/models")

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ChatReply:
        """One non-streaming chat completion. Retries 429/503 (2 s, 5 s); other errors and
        network failures raise UserFacingError."""
        body: dict[str, Any] = {"model": self.model, "messages": messages}
        if tools is not None:
            body["tools"] = tools
        if tool_choice is not None:
            body["tool_choice"] = tool_choice
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if temperature is not None:
            body["temperature"] = temperature

        delays = list(self.retry_delays_s)
        while True:
            try:
                response = await self._http.post("/v1/chat/completions", json=body)
            except httpx.HTTPError as e:
                raise UserFacingError(UNAVAILABLE) from e
            if response.status_code in RETRY_STATUSES and delays:
                await asyncio.sleep(delays.pop(0))
                continue
            if response.status_code != 200:
                raise UserFacingError(UNAVAILABLE)
            return _parse(response)


def _parse(response: httpx.Response) -> ChatReply:
    try:
        data = response.json()
        choice = data["choices"][0]
        message = choice.get("message") or {}
    except (ValueError, KeyError, IndexError, TypeError):
        raise UserFacingError(UNAVAILABLE)
    return ChatReply(
        content=(message.get("content") or "").strip(),
        tool_calls=message.get("tool_calls") or [],
        finish_reason=choice.get("finish_reason"),
        usage=data.get("usage"),
    )
