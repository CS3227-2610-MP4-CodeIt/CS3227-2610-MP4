"""Raw HTTP-status diagnostic for the complexity model catalog.

The app's LLMClient collapses every non-200 response into the same
UserFacingError("...unavailable...") after retrying 429/503 twice. That means
the model-selection probe cannot tell WHY a model scored 0/21:

  429  -> rate-limited; OUR fault (too much concurrency); re-runnable
  400  -> bad request; model likely not chat-capable for this body; ineligible
  404  -> unknown model; ineligible
  503  -> provider overloaded; transient
  200  -> model answered (schema failure is a real task result, not a call error)

This probe hits POST /v1/chat/completions DIRECTLY (bypassing the app client's
error swallowing) with a tiny prompt, once per model, concurrency capped at 8,
and reports the real status code so the results table can be made fair.

Run from backend/ (Python 3.14 venv):
    .venv/bin/python ../workflow/live-ai/model_status_probe.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.clients.llm import LLMClient, gateway_origin  # noqa: E402

SKIP_MODELS = {"bge-m3", "whisper-large-v3", "qwen3-vl:32b"}
_SEM = asyncio.Semaphore(8)  # match the main probe's concurrency cap


def _load_env() -> None:
    for line in (BACKEND / ".env").read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


async def _probe_status(http: httpx.AsyncClient, model: str) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
        "max_tokens": 16,
    }
    async with _SEM:
        start = time.monotonic()
        try:
            resp = await http.post("/v1/chat/completions", json=body, timeout=45.0)
        except httpx.HTTPError as exc:
            return {"model": model, "status": "transport_error", "detail": type(exc).__name__,
                    "latency": round(time.monotonic() - start, 2)}
        latency = round(time.monotonic() - start, 2)
    detail = ""
    if resp.status_code != 200:
        detail = resp.text[:160].replace("\n", " ")
    return {"model": model, "status": resp.status_code, "detail": detail, "latency": latency}


def _classify(status: object) -> str:
    if status == 200:
        return "answered (0/21 = real schema/task failure)"
    if status == 429:
        return "RATE-LIMITED (re-runnable, our concurrency)"
    if status == 400:
        return "bad request (model not chat-capable for this body)"
    if status == 404:
        return "unknown model"
    if status == 503:
        return "provider overloaded (transient)"
    if status == "transport_error":
        return "transport error / timeout"
    return "other"


async def main() -> int:
    _load_env()
    base, key = os.environ["SOCLAAS_BASE_URL"], os.environ["SOCLAAS_API_KEY"]
    probe = LLMClient(base, key, "default", 30.0)
    try:
        catalog = await probe.list_models()
    finally:
        await probe.aclose()
    models = [m for m in catalog if m not in SKIP_MODELS]
    print(f"Probing raw status for {len(models)} models (concurrency 8) ...", file=sys.stderr)

    http = httpx.AsyncClient(
        base_url=gateway_origin(base),
        headers={"Authorization": f"Bearer {key}"},
        timeout=45.0,
    )
    try:
        results = await asyncio.gather(*(_probe_status(http, m) for m in models))
    finally:
        await http.aclose()

    results.sort(key=lambda r: str(r["status"]))
    out = HERE / "model-status-diagnostic.md"
    lines = [
        "# Complexity catalog — raw HTTP status diagnostic",
        "",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S')}",
        "",
        "One minimal chat request per model, straight to POST /v1/chat/completions "
        "(bypassing the app client's error swallowing), concurrency capped at 8. "
        "Classifies why a model returned non-200 so the model-selection table is fair.",
        "",
        "| Model | HTTP status | classification | latency (s) | detail |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for r in results:
        lines.append(
            f"| `{r['model']}` | {r['status']} | {_classify(r['status'])} | "
            f"{r['latency']} | {r.get('detail', '')} |"
        )
        print(f"  {r['model']:24} {str(r['status']):>6}  {_classify(r['status'])}", file=sys.stderr)
    lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
