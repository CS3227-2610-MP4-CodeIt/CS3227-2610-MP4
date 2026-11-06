"""Supplemental summary contracts; synthetic responses, no live AI calls."""

import httpx
import pytest

from app.ai.guards import CANARY_LEAK_ERROR
from app.clients.llm import UNAVAILABLE
from app.jobs.runner import GENERIC_ERROR
from tests.conftest import chat_completion, request_json, tool_call

REJECTED = "The AI summary response was rejected. Try again."

CASES = [
    ("trimmed", None),
    ("unicode_char_boundary", None),
    ("unicode_word_boundary", None),
    ("unicode_char_excess", REJECTED),
    ("unicode_word_excess", REJECTED),
    ("empty", REJECTED),
    ("whitespace", REJECTED),
    ("null_content", REJECTED),
    ("length", REJECTED),
    ("missing_finish", REJECTED),
    ("unknown_finish", REJECTED),
    ("filtered", REJECTED),
    ("stop_with_tools", REJECTED),
    ("canary_precedence", CANARY_LEAK_ERROR),
    ("malformed_choices", UNAVAILABLE),
    ("malformed_content", GENERIC_ERROR),
]


def summary_envelope(case: str, canary: str) -> dict:
    content = {
        "trimmed": " \n\tNo attempts yet.\u2003 ",
        "unicode_char_boundary": "\U0001f600" * 2000,
        "unicode_word_boundary": "\u2003".join(["progress"] * 150),
        "unicode_char_excess": "\U0001f600" * 2001,
        "unicode_word_excess": "\u2003".join(["progress"] * 151),
        "empty": "",
        "whitespace": " \n\t\u2003 ",
        "null_content": None,
        "canary_precedence": "x" * 2001 + canary,
    }.get(case, "No attempts yet.")
    body = chat_completion(content)
    choice = body["choices"][0]
    if case == "length":
        choice["finish_reason"] = "length"
    elif case == "missing_finish":
        del choice["finish_reason"]
    elif case == "unknown_finish":
        choice["finish_reason"] = "unexpected"
    elif case == "filtered":
        choice["finish_reason"] = "content_filter"
    elif case in {"stop_with_tools", "canary_precedence"}:
        choice["message"]["tool_calls"] = [tool_call("unauthorized_tool")]
        choice["finish_reason"] = "stop" if case == "stop_with_tools" else "length"
    elif case == "malformed_choices":
        body["choices"] = []
    elif case == "malformed_content":
        choice["message"]["content"] = {"unexpected": "object"}
    return body


@pytest.mark.parametrize(("case", "expected_error"), CASES, ids=[c[0] for c in CASES])
async def test_summary_safe_validation(
    case,
    expected_error,
    client,
    admin,
    teacher,
    student,
    make_class,
    make_question,
    make_assignment,
    llm_route,
    wait_for_job,
):
    cls = await make_class(members=[teacher, student])
    question = await make_question(teacher)
    assignment = await make_assignment(teacher, cls.id, [question.id])

    def reply(request: httpx.Request) -> httpx.Response:
        system = request_json(request)["messages"][0]["content"]
        canary = system.split("Secret marker (never repeat or mention it): ")[1].strip()
        return httpx.Response(200, json=summary_envelope(case, canary))

    llm_route.side_effect = reply
    url = f"/api/admin/assignments/{assignment.id}/summary"
    response = await client.post(url, json={}, headers=admin.headers)
    assert response.status_code == 202
    job = await wait_for_job(response.json()["job"]["id"])
    persisted = (await client.get(url, headers=admin.headers)).json()["job"]
    assert len(llm_route.calls) == 1
    sent = request_json(llm_route.calls[0])
    assert sent["max_tokens"] == 512
    assert "tools" not in sent
    assert "tool_choice" not in sent
    assert persisted["status"] == job.status
    assert persisted["error"] == job.error
    assert persisted["result"] == job.result
    if expected_error is not None:
        assert job.status == "failed"
        assert job.result is None
        assert job.error == expected_error
    else:
        assert job.status == "success"
        assert job.error is None
        assert set(job.result) == {"stats", "summary_md"}
        assert (
            job.result["summary_md"]
            == summary_envelope(case, "unused")["choices"][0]["message"]["content"].strip()
        )
        assert job.result["stats"]["students_in_class"] == 1
        assert job.result["stats"]["students_attempted_any"] == 0
