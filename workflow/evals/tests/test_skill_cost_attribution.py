"""Tests for turn-anchored per-skill cost attribution.

Per-skill cost must come ONLY from turns that map to exactly one skill. Turns
that see more than one skill are ambiguous and are left in a shared bucket — a
skill never accrues a fabricated or split cost. These tests pin that contract.

Run with:  python3 -m pytest tests/ -q  (from workflow/evals)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from _lib.usage import (  # noqa: E402
    build_project_usage,
    discover_project_inventory,
    parse_session_rollout,
    render_usage_html,
)


def _write_rollout(path: Path, records: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    return path


def _make_project(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "proj"
    evals_root = project_root / "workflow" / "evals"
    evals_root.mkdir(parents=True, exist_ok=True)
    for name in ("code-review", "logging"):
        skill = project_root / ".agents" / "skills" / name / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(f"---\nname: {name}\n---\n# {name}\n", encoding="utf-8")
    return project_root, evals_root


def _skill_block(project_root: Path, name: str) -> dict:
    return {
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "<skill>\n"
                        f"<name>{name}</name>\n"
                        f"<path>{project_root}/.agents/skills/{name}/SKILL.md</path>\n"
                        "</skill>"
                    ),
                }
            ],
        },
    }


def _priced(rid: str, turn: str, inp: int = 150000, out: int = 153) -> dict:
    # gpt-6.1-sol is a priced model in the fixture pricing table.
    return {
        "type": "token_usage_record",
        "timestamp": "2026-04-20T10:00:09Z",
        "payload": {
            "thread_id": "thread-1",
            "turn_id": turn,
            "root_turn_id": turn,
            "response_id": rid,
            "model": "gpt-6.1-sol",
            "usage": {
                "input_tokens": inp,
                "output_tokens": out,
                "reasoning_output_tokens": min(17, out),
            },
        },
    }


def test_turn_skills_captured_per_turn(tmp_path):
    project_root, _ = _make_project(tmp_path)
    rollout = _write_rollout(
        tmp_path / "sessions" / "rollout-x.jsonl",
        [
            {
                "timestamp": "2026-04-20T10:00:00Z",
                "type": "session_meta",
                "payload": {"id": "thread-1", "timestamp": "2026-04-20T10:00:00Z", "cwd": str(project_root)},
            },
            {"type": "turn_context", "payload": {"turn_id": "t-rev", "root_turn_id": "t-rev", "model": "gpt-6.1-sol"}},
            _skill_block(project_root, "code-review"),
            {"type": "turn_context", "payload": {"turn_id": "t-both", "root_turn_id": "t-both", "model": "gpt-6.1-sol"}},
            _skill_block(project_root, "code-review"),
            _skill_block(project_root, "logging"),
        ],
    )
    parsed = parse_session_rollout(rollout)
    # Each turn records exactly the skills observed during it.
    assert parsed["turn_skills"]["t-rev"] == ["code-review"]
    assert parsed["turn_skills"]["t-both"] == ["code-review", "logging"]
    # Flat set still works for existing consumers.
    assert parsed["skills_used"] == ["code-review", "logging"]


def _build(tmp_path):
    project_root, evals_root = _make_project(tmp_path)
    rollout = _write_rollout(
        tmp_path / "sessions" / "rollout-main.jsonl",
        [
            {
                "timestamp": "2026-04-20T10:00:00Z",
                "type": "session_meta",
                "payload": {"id": "thread-1", "timestamp": "2026-04-20T10:00:00Z", "cwd": str(project_root)},
            },
            # Turn t-rev: only code-review observed -> attributable.
            {"type": "turn_context", "payload": {"turn_id": "t-rev", "root_turn_id": "t-rev", "model": "gpt-6.1-sol"}},
            _skill_block(project_root, "code-review"),
            _priced("req-rev", "t-rev"),
            # Turn t-both: code-review AND logging observed -> shared/ambiguous.
            {"type": "turn_context", "payload": {"turn_id": "t-both", "root_turn_id": "t-both", "model": "gpt-6.1-sol"}},
            _skill_block(project_root, "code-review"),
            _skill_block(project_root, "logging"),
            _priced("req-both", "t-both"),
        ],
    )
    parsed = parse_session_rollout(rollout)
    entries = {str(rollout): parsed}
    summary = build_project_usage(
        rollouts_by_path=entries, project_root=project_root, evals_root=evals_root
    )
    return summary


def test_single_skill_turn_cost_is_attributed_shared_turn_is_not(tmp_path):
    summary = _build(tmp_path)
    by_name = {s["skill"]: s for s in summary["skills"]}

    review = by_name["code-review"]
    logging = by_name["logging"]

    # code-review uniquely owns t-rev -> its priced cost is attributed.
    assert review["priced_count"] == 1
    assert review["est_cost"] > 0
    # code-review also appeared in the shared turn t-both, which must NOT be
    # charged to it; the skill is flagged as having shared turns.
    assert review["shared_turn_count"] == 1
    assert review["attributed_turn_count"] == 1
    assert review["cost_status"] == "attributed_shared"

    # logging ONLY appeared in the shared turn -> no cost, flagged shared.
    assert logging["priced_count"] == 0
    assert logging["est_cost"] == 0.0
    assert logging["shared_turn_count"] == 1
    assert logging["cost_status"] == "shared"

    # The shared turn's cost is never split across skills: the two skills'
    # attributed cost together equals only the single-skill turn's cost.
    assert review["est_cost"] + logging["est_cost"] == review["est_cost"]


def test_no_fabricated_identical_costs(tmp_path):
    """Regression guard: skills must not all show the same fabricated figure."""
    summary = _build(tmp_path)
    triggered = [s for s in summary["skills"] if s["sessions_triggered"] > 0]
    costs = sorted(s["est_cost"] for s in triggered)
    # Exactly one triggered skill carries a real cost; the shared-only skill is
    # zero. The old bug made every skill show the same fabricated total.
    assert costs == [0.0, pytest.approx(0.30153)]
    assert len({c for c in costs}) == 2


def test_attributable_cost_renders_meter_and_shared_label(tmp_path):
    summary = _build(tmp_path)
    html = render_usage_html(summary)
    # The attributed skill shows a cost meter bar.
    assert "table-cost" in html and "meter-blue" in html
    # A shared-only skill now shows a clean $0.00 (meaning unattributable /
    # shared) rather than a muted word, with the caveat moved to a tooltip so
    # the zero is not misread as literally free.
    assert "shared / ambiguous" not in html
    assert "counted once at the session level" in html
    # The coverage panel is styled as a card, not a raw dump.
    assert "coverage-card" in html and "coverage-stats" in html
