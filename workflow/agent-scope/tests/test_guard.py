"""Tests for the agent-scope guard.

Run from this folder: python3 -m pytest workflow/agent-scope/tests -q
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

GUARD_PATH = Path(__file__).resolve().parent.parent / "guard.py"
_spec = importlib.util.spec_from_file_location("agent_scope_guard", GUARD_PATH)
guard = importlib.util.module_from_spec(_spec)
sys.modules["agent_scope_guard"] = guard
_spec.loader.exec_module(guard)


# --- policy matching -------------------------------------------------------


def make_policy(allow, block=()):
    return guard.ScopePolicy("sample", tuple(allow), tuple(block))


def test_allow_match_permits():
    policy = make_policy(["backend/**"])
    assert policy.permits("backend/app/routers/student.py")


def test_unlisted_path_denied():
    policy = make_policy(["backend/**"])
    assert not policy.permits("frontend/src/main.tsx")


def test_block_overrides_allow():
    policy = make_policy(["backend/**"], ["**/.env", "**/.env.*"])
    assert not policy.permits("backend/.env")
    assert not policy.permits("backend/.env.local")


def test_empty_allow_forbids_everything():
    policy = make_policy([], [])
    assert not policy.permits("anything.py")


def test_reviewer_confined_to_reviews_tree():
    policy = make_policy(["workflow/reviews/**"])
    assert policy.permits("workflow/reviews/run-7/code-quality.md")
    assert not policy.permits("backend/app/main.py")


# --- ledger loading from the real policy -----------------------------------


def test_real_policy_loads_six_roles():
    ledger = guard.ScopeLedger.load()
    assert set(ledger.by_role) == {
        "task_implementer",
        "code_quality_reviewer",
        "spec_contract_reviewer",
        "security_boundary_reviewer",
        "verification_reviewer",
        "review_aggregator",
    }


def test_implementer_cannot_write_reviews_or_env():
    ledger = guard.ScopeLedger.load()
    impl = ledger.by_role["task_implementer"]
    assert impl.permits("backend/app/routers/student.py")
    assert impl.permits("specs/backend-spec.md")
    assert not impl.permits("workflow/reviews/run-1/report.md")
    assert not impl.permits("backend/.env")


def test_unknown_role_is_unrestricted():
    ledger = guard.ScopeLedger.load()
    assert ledger.policy_for("orchestrator") is None
    assert ledger.policy_for(None) is None


def test_schema_mismatch_rejected(tmp_path):
    bad = tmp_path / "scope.toml"
    bad.write_text("schema = 99\n[roles.x]\nallow = []\nblock = []\n", encoding="utf-8")
    with pytest.raises(ValueError):
        guard.ScopeLedger.load(bad)


# --- bash target extraction ------------------------------------------------


@pytest.mark.parametrize(
    "command,expected",
    [
        ("echo hi > backend/app/new.py", ["backend/app/new.py"]),
        ("cat a.py >> workflow/reviews/x.md", ["workflow/reviews/x.md"]),
        ("cp src.py frontend/dst.py", ["frontend/dst.py"]),
        ("touch backend/a.py backend/b.py", ["backend/a.py", "backend/b.py"]),
        ("sed -i s/x/y/ backend/app/main.py", ["backend/app/main.py"]),
        ("ls backend/app", []),
        ("cat backend/app/main.py", []),
    ],
)
def test_bash_write_targets(command, expected):
    assert guard._targets_in_bash(command) == expected


def test_unparseable_bash_yields_no_targets():
    assert guard._targets_in_bash("echo 'unterminated") == []


# --- apply_patch target extraction -----------------------------------------


def test_patch_update_file_target():
    body = "*** Begin Patch\n*** Update File: backend/app/main.py\n@@\n-a\n+b\n*** End Patch"
    assert guard._targets_in_patch(body) == ["backend/app/main.py"]


def test_patch_add_and_delete_targets():
    body = (
        "*** Begin Patch\n"
        "*** Add File: frontend/src/new.tsx\n+x\n"
        "*** Delete File: backend/app/old.py\n"
        "*** End Patch"
    )
    assert guard._targets_in_patch(body) == ["frontend/src/new.tsx", "backend/app/old.py"]


def test_patch_absolute_path_normalized_and_checked():
    # The real captured payload: a reviewer editing .env via apply_patch.
    abs_env = str((guard.REPO / ".env").resolve())
    body = f"*** Begin Patch\n*** Update File: {abs_env}\n@@\n-hi\n+hello\n*** End Patch"
    rel = guard._repo_relative(guard._targets_in_patch(body)[0])
    assert rel == ".env"
    reviewer = guard.ScopeLedger.load().by_role["code_quality_reviewer"]
    assert not reviewer.permits(rel)


def test_written_targets_dispatches_by_tool():
    assert guard._written_targets("apply_patch", {"command": "*** Update File: a.py\n"}) == ["a.py"]
    assert guard._written_targets("Bash", {"command": "echo x > a.py"}) == ["a.py"]
    assert guard._written_targets("collaborationspawn_agent", {"message": "go"}) == []


# --- guard mode (stdin payload) --------------------------------------------


def run_guard_with(payload):
    return guard.run_guard(io.StringIO(json.dumps(payload)))


def test_guard_blocks_reviewer_writing_source():
    payload = {
        "tool_name": "Bash",
        "agent_type": "code_quality_reviewer",
        "tool_input": {"command": "echo x > backend/app/main.py"},
    }
    assert run_guard_with(payload) == 2


def test_guard_allows_reviewer_writing_its_artifact():
    payload = {
        "tool_name": "Bash",
        "agent_type": "code_quality_reviewer",
        "tool_input": {"command": "echo x > workflow/reviews/run/cq.md"},
    }
    assert run_guard_with(payload) == 0


def test_guard_allows_unknown_role():
    payload = {
        "tool_name": "Bash",
        "agent_type": "orchestrator",
        "tool_input": {"command": "echo x > backend/app/main.py"},
    }
    assert run_guard_with(payload) == 0


def test_guard_allows_read_only_bash_for_scoped_role():
    payload = {
        "tool_name": "Bash",
        "agent_type": "task_implementer",
        "tool_input": {"command": "uv run pytest -q"},
    }
    assert run_guard_with(payload) == 0


def test_guard_fails_closed_on_garbage_stdin():
    assert guard.run_guard(io.StringIO("not json")) == 2


def test_guard_blocks_reviewer_apply_patch_on_source():
    # Mirrors the real captured payload: code_quality_reviewer apply_patch on .env.
    abs_env = str((guard.REPO / ".env").resolve())
    payload = {
        "tool_name": "apply_patch",
        "agent_type": "code_quality_reviewer",
        "tool_input": {
            "command": f"*** Begin Patch\n*** Update File: {abs_env}\n@@\n-hi\n+hello\n*** End Patch"
        },
    }
    assert run_guard_with(payload) == 2


def test_guard_allows_reviewer_apply_patch_in_reviews_tree():
    abs_art = str((guard.REPO / "workflow/reviews/run/cq.md").resolve())
    payload = {
        "tool_name": "apply_patch",
        "agent_type": "code_quality_reviewer",
        "tool_input": {
            "command": f"*** Begin Patch\n*** Add File: {abs_art}\n+notes\n*** End Patch"
        },
    }
    assert run_guard_with(payload) == 0


def test_guard_ignores_non_write_spawn_tool():
    payload = {
        "tool_name": "collaborationspawn_agent",
        "agent_type": "task_implementer",
        "tool_input": {"task_name": "x", "message": "go"},
    }
    assert run_guard_with(payload) == 0

def test_heredoc_body_not_scanned_for_redirects():
    # A python heredoc whose BODY contains '>' must not yield a target from the
    # body (regression: 'max_output_tokens > 5000' produced the path '5000').
    cmd = "python3 - <<'PY'\nx = 1 if a > 5000 else 0\nopen('p','w')\nPY"
    assert guard._targets_in_bash(cmd) == []

def test_heredoc_with_leading_redirect_still_caught():
    # `cat > file <<EOF` redirects to file THEN reads a here-doc; the file
    # target precedes '<<' so it is still captured.
    cmd = "cat > workflow/reviews/r.md <<'EOF'\nhello\nEOF"
    assert guard._targets_in_bash(cmd) == ["workflow/reviews/r.md"]

def test_append_heredoc_target_caught():
    cmd = "cat >> backend/tests/test_x.py <<'EOF'\nbody\nEOF"
    assert guard._targets_in_bash(cmd) == ["backend/tests/test_x.py"]
