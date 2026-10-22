"""Student hint: a bounded tool loop (spec §7.1)."""

from pathlib import Path
from typing import Any

from app.ai import guards
from app.config import AppContext
from app.jobs.runner import UserFacingError
from app.repos import questions as questions_repo

MAX_TOOL_ROUNDS = 3
MAX_TOKENS = 1024
_BASE_PROMPT = (Path(__file__).parent / "prompts" / "hint.md").read_text()

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": {}},
        },
    }
    for name, description in (
        ("get_question", "Get the question: title, statement, limits and the visible test cases."),
        ("get_code", "Get the student's current code."),
    )
]


async def run_hint(ctx: AppContext, job_input: dict[str, Any]) -> dict[str, Any]:
    question = await questions_repo.get(ctx.db, job_input["question_id"])
    if question is None:
        raise UserFacingError("The question no longer exists.")
    code: str = job_input["code"]
    visible = [t for t in question.test_cases if not t.is_hidden]

    def get_question() -> str:
        lines = [
            f"Title: {question.title}",
            f"Time limit: {question.time_limit_ms} ms, memory limit: {question.memory_limit_mb} MB",
            "",
            question.statement_md,
            "",
            "Visible test cases:",
        ]
        for i, t in enumerate(visible, 1):
            lines += [f"Test {i} input:", t.stdin, f"Test {i} expected output:", t.expected_stdout]
        return "\n".join(lines)

    handlers = {"get_question": get_question, "get_code": lambda: code}

    nonce = guards.new_nonce()
    canary = guards.new_canary()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": guards.build_system_prompt(_BASE_PROMPT, nonce, canary)},
        {
            "role": "user",
            "content": f"The student is stuck on the question {guards.wrap_untrusted('title', question.title, nonce)} and asks for a hint. "
            "Use the tools to read the question and/or their code if you need them.",
        },
    ]
    tools_used: list[str] = []

    reply = await ctx.llm.chat(messages, tools=TOOLS, tool_choice="auto", max_tokens=MAX_TOKENS)
    for round_no in range(1, MAX_TOOL_ROUNDS + 1):
        if not reply.tool_calls:
            break
        messages.append(reply.assistant_message())
        for call in reply.tool_calls:
            name = call.get("function", {}).get("name", "")
            handler = handlers.get(name)
            if handler is None:
                content = "unknown tool"
            else:
                if name not in tools_used:
                    tools_used.append(name)
                content = guards.wrap_untrusted(name, handler(), nonce)
            messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": content})
        choice = "none" if round_no == MAX_TOOL_ROUNDS else "auto"
        reply = await ctx.llm.chat(messages, tools=TOOLS, tool_choice=choice, max_tokens=MAX_TOKENS)

    hint = guards.check_hint_output(reply.content, canary)
    if not hint:
        raise UserFacingError("The AI response was empty. Try again.")
    return {"hint_md": hint, "tools_used": tools_used}
