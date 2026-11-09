import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.ai import hints
from app.clients.llm import ChatReply
from app.jobs.runner import UserFacingError


@pytest.mark.parametrize(
    "raw",
    [
        "{}",
        '{"is_hint":1,"reveals_answer":false}',
        '{"is_hint":true,"reveals_answer":false,"extra":0}',
        'text {"is_hint":true,"reveals_answer":false}',
        '{"is_hint":true,"is_hint":false,"reveals_answer":false}',
        '{"is_hint":true,"reveals_answer":false} trailing',
        "[]",
    ],
)
def test_strict_verdict_rejects_invalid_json_or_schema(raw):
    with pytest.raises(ValueError):
        hints._strict_verdict(raw)


@pytest.mark.parametrize(
    ("is_hint", "reveals", "withheld"),
    [
        (True, False, False),
        (False, False, True),
        (True, True, True),
        (False, True, True),
    ],
)
async def test_review_verdict_combinations(is_hint, reveals, withheld):
    reply = ChatReply(
        content=f'{{"is_hint":{str(is_hint).lower()},"reveals_answer":{str(reveals).lower()}}}'
    )
    ctx = SimpleNamespace(
        llm=SimpleNamespace(chat=AsyncMock(return_value=reply)),
        settings=SimpleNamespace(hint_reviewer_model="reviewer"),
    )
    question = SimpleNamespace(
        test_cases=[SimpleNamespace(is_hidden=True, expected_stdout="answer")]
    )
    if withheld:
        with pytest.raises(UserFacingError):
            await hints._review_hint(ctx, question, "question", "hint", None)
    else:
        await hints._review_hint(ctx, question, "question", "hint", None)


async def test_review_limits_and_failure_do_not_log_content(caplog, monkeypatch):
    ctx = SimpleNamespace(
        llm=SimpleNamespace(chat=AsyncMock(side_effect=RuntimeError("secret answer"))),
        settings=SimpleNamespace(hint_reviewer_model="reviewer"),
    )
    question = SimpleNamespace(
        test_cases=[SimpleNamespace(is_hidden=True, expected_stdout="secret answer")]
    )
    with caplog.at_level(logging.WARNING):
        await hints._review_hint(ctx, question, "question", "candidate", None)
        await hints._review_hint(ctx, question, "x" * hints.REVIEW_MAX_BYTES, "candidate", None)
        await hints._review_hint(
            ctx, question, "question", "candidate", asyncio.get_running_loop().time()
        )
    assert ctx.llm.chat.await_count == 1
    assert "secret answer" not in caplog.text and "candidate" not in caplog.text
    assert "too large" in caplog.text and "insufficient time" in caplog.text


async def test_review_canary_and_timeout_fail_open(monkeypatch, caplog):
    question = SimpleNamespace(test_cases=[])
    monkeypatch.setattr(hints.guards, "new_canary", lambda: "CANARY-test")
    ctx = SimpleNamespace(
        llm=SimpleNamespace(chat=AsyncMock(return_value=ChatReply(content="CANARY-test"))),
        settings=SimpleNamespace(hint_reviewer_model="reviewer"),
    )
    await hints._review_hint(ctx, question, "question", "hint", None)

    async def slow(*args, **kwargs):
        await asyncio.sleep(1)

    ctx.llm.chat = AsyncMock(side_effect=slow)
    monkeypatch.setattr(hints, "REVIEW_TIMEOUT_S", 0.001)
    await hints._review_hint(ctx, question, "question", "hint", None)
    assert "CANARY-test" not in caplog.text


async def test_review_does_not_swallow_job_cancellation():
    async def cancelled(*args, **kwargs):
        raise asyncio.CancelledError

    ctx = SimpleNamespace(
        llm=SimpleNamespace(chat=AsyncMock(side_effect=cancelled)),
        settings=SimpleNamespace(hint_reviewer_model="reviewer"),
    )
    with pytest.raises(asyncio.CancelledError):
        await hints._review_hint(ctx, SimpleNamespace(test_cases=[]), "question", "hint", None)


async def test_unexpected_reviewer_failure_has_distinct_safe_diagnostic(caplog):
    question = SimpleNamespace(test_cases=[])
    ctx = SimpleNamespace(
        llm=SimpleNamespace(chat=AsyncMock(side_effect=AttributeError("private exception text"))),
        settings=SimpleNamespace(hint_reviewer_model="reviewer"),
    )
    await hints._review_hint(ctx, question, "question", "hint", None)
    assert "unexpected" in caplog.text.lower()
    assert "private exception text" not in caplog.text


async def test_expected_reviewer_failure_has_safe_distinct_diagnostic(caplog):
    ctx = SimpleNamespace(
        llm=SimpleNamespace(chat=AsyncMock(side_effect=UserFacingError("sensitive details"))),
        settings=SimpleNamespace(hint_reviewer_model="reviewer"),
    )
    await hints._review_hint(ctx, SimpleNamespace(test_cases=[]), "question", "hint", None)
    assert "invalid verdict" in caplog.text.lower() and "unexpected" not in caplog.text.lower()
    assert "sensitive details" not in caplog.text
