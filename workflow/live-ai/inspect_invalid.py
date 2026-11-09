"""One-off: show WHY a given model's replies fail ComplexityResult validation.

Runs the real complexity pipeline (prompt + guards) against one model over the
fixtures and, for each reply, prints the raw content and the exact failure:
JSON parse error, pydantic validation error, canary leak, or size/tool-call.

Run from backend/ (Python 3.14 venv):
    .venv/bin/python ../workflow/live-ai/inspect_invalid.py qwen3.5:9b
    .venv/bin/python ../workflow/live-ai/inspect_invalid.py qwen3.5:9b --trials 1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.ai import guards  # noqa: E402
from app.ai.complexity import ComplexityResult  # noqa: E402
from app.clients.llm import LLMClient  # noqa: E402

from complexity_fixtures import CASES  # noqa: E402
from complexity_model_selection import COMPLEXITY_PROMPT, _load_env  # noqa: E402


async def _one(client: LLMClient, code: str) -> tuple[str, str]:
    """Returns (raw_reply_content, diagnosis)."""
    nonce, canary = guards.new_nonce(), guards.new_canary()
    messages = [
        {"role": "system", "content": guards.build_system_prompt(COMPLEXITY_PROMPT, nonce, canary)},
        {"role": "user", "content": guards.wrap_untrusted("submitted_code", code, nonce)},
    ]
    try:
        reply = await client.chat(messages, max_tokens=1500)
    except Exception as exc:  # noqa: BLE001
        return "", f"CALL ERROR: {type(exc).__name__}: {exc}"
    content = reply.content
    try:
        guards.check_canary(content, canary)
    except Exception as exc:  # noqa: BLE001
        return content, f"CANARY LEAK: {exc}"
    if reply.tool_calls:
        return content, f"TOOL CALLS: {reply.tool_calls}"
    if len(content) > 5000:
        return content, f"TOO LONG: {len(content)} chars"
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        return content, f"JSON PARSE ERROR: {exc}"
    try:
        ComplexityResult.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        return content, f"SCHEMA ERROR: {exc}"
    return content, "OK"


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--trials", type=int, default=2)
    args = ap.parse_args()

    _load_env()
    base, key = os.environ["SOCLAAS_BASE_URL"], os.environ["SOCLAAS_API_KEY"]
    client = LLMClient(base, key, args.model, chat_timeout_s=60.0)
    try:
        for case in CASES:
            for t in range(args.trials):
                start = time.monotonic()
                content, diag = await _one(client, case.code)
                dt = time.monotonic() - start
                print("=" * 78)
                print(f"[{case.name}] trial {t + 1}  ({dt:.1f}s)  -> {diag.splitlines()[0]}")
                print("-" * 78)
                print(content if content else "(empty / no content)")
                if not diag.startswith("OK"):
                    print("-" * 78)
                    print(diag)
                print()
    finally:
        await client.aclose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
