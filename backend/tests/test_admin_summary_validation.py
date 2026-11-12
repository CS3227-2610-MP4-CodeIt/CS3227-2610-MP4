"""Supplemental summary contracts; synthetic responses, no live AI calls."""

import json

import httpx
import pytest

from app.ai.guards import CANARY_LEAK_ERROR
from app.clients.llm import UNAVAILABLE
from app.jobs.runner import GENERIC_ERROR
from tests.conftest import chat_completion, request_json, tool_call

REJECTED = "The AI summary response was rejected. Try again."

CASES = [
    ("trimmed", None),
    ("prompt_word_target", None),
    ("above_prompt_target", None),
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
        "prompt_word_target": " ".join(["progress"] * 120),
        "above_prompt_target": " ".join(["progress"] * 121),
        "unicode_char_boundary": "\U0001f600" * 2000,
        "unicode_word_boundary": "\u2003".join(["word"] * 250),
        "unicode_char_excess": "\U0001f600" * 2001,
        "unicode_word_excess": "\u2003".join(["word"] * 251),
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
    system = sent["messages"][0]["content"]
    assert "100–120 words" in system
    assert "never exceed 120 words" in system
    assert "within 2,000 characters" in system
    assert "participation (students who attempted any question)" in system
    assert "completion (students who solved all questions)" in system
    assert "hardest question only where supported" in system
    assert "acknowledge ties or insufficient evidence" in system
    assert "failure verdict(s) where supported" in system
    assert "if there are no failures, say so" in system
    assert "Do not invent statistics" in system
    assert "unsupported conclusions" in system
    assert sent["max_tokens"] == 768
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


async def test_three_question_summary_aggregates(
    client,
    admin,
    teacher,
    student,
    make_class,
    make_question,
    make_assignment,
    llm_route,
    wait_for_job,
    ctx,
):
    from app.repos import submissions as submissions_repo

    cls = await make_class(members=[teacher, student])
    questions = [await make_question(teacher, title=f"Question {i}") for i in range(3)]
    assignment = await make_assignment(teacher, cls.id, [q.id for q in questions])
    for index, verdict in [
        (0, "WRONG_ANSWER"),
        (0, "ACCEPTED"),
        (1, "ACCEPTED"),
        (2, "RUNTIME_ERROR"),
    ]:
        await submissions_repo.create(
            ctx.db,
            student.id,
            assignment.id,
            questions[index].id,
            None,
            "private-code-sentinel",
            verdict,
            int(verdict == "ACCEPTED"),
            1,
        )
    llm_route.side_effect = [httpx.Response(200, json=chat_completion("Partial completion."))]
    response = await client.post(
        f"/api/admin/assignments/{assignment.id}/summary", json={}, headers=admin.headers
    )
    assert response.status_code == 202
    job = await wait_for_job(response.json()["job"]["id"])
    assert job.status == "success"
    stats = job.result["stats"]
    assert stats["students_in_class"] == 1
    assert stats["students_attempted_any"] == 1
    assert stats["students_solved_all"] == 0
    rows = stats["questions"]
    assert [r["position"] for r in rows] == [1, 2, 3]
    assert [r["attempted"] for r in rows] == [1, 1, 1]
    assert [r["correct"] for r in rows] == [1, 1, 0]
    assert [r["total_submissions"] for r in rows] == [2, 1, 1]
    for row, expected in zip(
        rows,
        [{"WRONG_ANSWER": 1, "ACCEPTED": 1}, {"ACCEPTED": 1}, {"RUNTIME_ERROR": 1}],
        strict=True,
    ):
        assert row["verdicts"] == {v: expected.get(v, 0) for v in submissions_repo.VERDICTS}
    assert len(llm_route.calls) == 1
    sent = request_json(llm_route.calls[0])
    assert sent["max_tokens"] == 768
    assert "tools" not in sent
    data = sent["messages"][1]["content"]
    assert json.loads(data.split("\n", 1)[1].rsplit("\n", 1)[0]) == stats
    assert "private-code-sentinel" not in data
    assert student.user.username not in data
