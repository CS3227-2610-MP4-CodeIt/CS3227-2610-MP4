"""Synthetic replies only: rejection logs must contain no response-derived data."""

import logging

import pytest

from app.ai import guards, summary
from app.clients.llm import ChatReply
from app.jobs.runner import UserFacingError

PRIVATE = "private-response-sentinel"
CANARY = "CANARY-test-secret"


@pytest.mark.parametrize(
    ("reply", "reason", "error"),
    [
        (ChatReply(PRIVATE, finish_reason="length"), "finish_length", summary._SUMMARY_REJECTED),
        (ChatReply(PRIVATE), "finish_missing", summary._SUMMARY_REJECTED),
        (ChatReply(PRIVATE, finish_reason=""), "finish_other", summary._SUMMARY_REJECTED),
        (ChatReply(PRIVATE, finish_reason=PRIVATE), "finish_other", summary._SUMMARY_REJECTED),
        (
            ChatReply(PRIVATE, finish_reason="content_filter"),
            "finish_other",
            summary._SUMMARY_REJECTED,
        ),
        (
            ChatReply(PRIVATE, tool_calls=[{"arguments": PRIVATE}], finish_reason="stop"),
            "unexpected_tools",
            summary._SUMMARY_REJECTED,
        ),
        (ChatReply(" \n\t", finish_reason="stop"), "empty", summary._SUMMARY_REJECTED),
        (
            ChatReply(PRIVATE + " word" * 250, finish_reason="stop"),
            "word_limit",
            summary._SUMMARY_REJECTED,
        ),
        (
            ChatReply(PRIVATE * 100, finish_reason="stop"),
            "character_limit",
            summary._SUMMARY_REJECTED,
        ),
        (
            ChatReply(PRIVATE * 100 + CANARY, finish_reason="length"),
            "canary_detected",
            guards.CANARY_LEAK_ERROR,
        ),
        (
            ChatReply("", tool_calls=[{"arguments": PRIVATE}], finish_reason="length"),
            "finish_length",
            summary._SUMMARY_REJECTED,
        ),
    ],
)
def test_rejection_logs_only_fixed_reason(caplog, reply, reason, error):
    with caplog.at_level(logging.WARNING, logger="app.ai.summary"):
        with pytest.raises(UserFacingError) as exc:
            summary._validate_summary_reply(reply, CANARY)
    assert str(exc.value) == error
    assert [(r.name, r.levelname, r.getMessage()) for r in caplog.records] == [
        ("app.ai.summary", "WARNING", f"Admin summary validation rejected: {reason}")
    ]
    assert PRIVATE not in caplog.text
    assert CANARY not in caplog.text
    assert caplog.records[0].exc_info is None
    assert caplog.records[0].stack_info is None


@pytest.mark.parametrize(
    "text",
    [PRIVATE, " ".join(["word"] * 151), " ".join(["word"] * 250), "x" * 2000],
)
def test_accepted_reply_is_unchanged_and_silent(caplog, text):
    with caplog.at_level(logging.WARNING, logger="app.ai.summary"):
        assert (
            summary._validate_summary_reply(ChatReply(text, finish_reason="stop"), CANARY) == text
        )
    assert not caplog.records
