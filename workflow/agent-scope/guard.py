#!/usr/bin/env python3
"""Enforce CodeIt's per-role agent write scope (see scope.toml).

This tool keeps a delegated Codex role inside the file boundary its human
authored. It is deliberately split into a live guard and an authoritative audit,
because Codex's PreToolUse event only observes Bash commands in the versions we
target: it cannot see an ``apply_patch`` edit. So the live guard is a tripwire
for shell writes, and the diff audit is the real acceptance check the
orchestrator runs after a role returns.

Modes
  guard   Read a Codex PreToolUse payload on stdin and refuse a Bash command
          that would write outside the acting role's scope. Prints the refusal
          on stderr and exits 2 (Codex blocks on exit 2). Anything it cannot
          confidently classify is allowed through, since the diff audit is the
          backstop; a missing policy or unreadable payload instead fails closed.

  audit   Compare the working tree against a baseline commit and report every
          changed path the named role may not write. Exit 1 on a violation or a
          moved HEAD, else 0. This is the authoritative check.

  verify  Confirm a previously recorded manifest still describes the working
          tree, for holding a review candidate steady. Exit 1 on drift.

  pin     Record the baseline manifest (HEAD plus tracked-path digests) that
          ``verify`` compares against. Writes outside the repository only.

The policy source is scope.toml beside this file. Roles, patterns and matching
rules are documented there.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shlex
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
POLICY_FILE = HERE / "scope.toml"

# Bash words that place content at their final path argument. Enough to catch the
# common shell write vectors; the diff audit covers whatever slips past.
_REDIRECTS = (">", ">>")
_WRITE_VERBS = {"cp", "mv", "touch", "tee", "install"}
_INPLACE = {"sed": "-i", "perl": "-i"}

# apply_patch envelope lines that name a file the patch will write. The patch
# body lives in tool_input.command; paths may be absolute or repo-relative.
_PATCH_FILE_LINE = re.compile(
    r"^\*\*\*\s+(?:Add|Update|Delete|Move\s+to)\s+File:\s+(.+?)\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class ScopePolicy:
    """One role's allow/block lists, as authored in scope.toml."""

    role: str
    allow: tuple[str, ...]
    block: tuple[str, ...]

    def permits(self, rel_path: str) -> bool:
        """True when a repo-relative path is writable under this policy."""
        if any(fnmatch.fnmatch(rel_path, pat) for pat in self.block):
            return False
        return any(fnmatch.fnmatch(rel_path, pat) for pat in self.allow)


@dataclass
class ScopeLedger:
    """The full set of role policies loaded from scope.toml."""

    by_role: dict[str, ScopePolicy] = field(default_factory=dict)

    @classmethod
    def load(cls, source: Path = POLICY_FILE) -> ScopeLedger:
        raw = tomllib.loads(source.read_text(encoding="utf-8"))
        if raw.get("schema") != 1:
            raise ValueError(f"{source}: unsupported policy schema")
        roles = raw.get("roles")
        if not isinstance(roles, dict) or not roles:
            raise ValueError(f"{source}: no roles defined")
        ledger = cls()
        for name, body in roles.items():
            allow = tuple(body.get("allow", []))
            block = tuple(body.get("block", []))
            if not all(isinstance(p, str) for p in (*allow, *block)):
                raise ValueError(f"{source}: role '{name}' has a non-string pattern")
            ledger.by_role[name] = ScopePolicy(name, allow, block)
        return ledger

    def policy_for(self, role: str | None) -> ScopePolicy | None:
        """The policy for a role, or None when the role is unrestricted."""
        if not role:
            return None
        return self.by_role.get(role)


def _repo_relative(path: str, root: Path = REPO) -> str | None:
    """Return the path relative to the repo root, or None if it escapes it."""
    try:
        rel = (root / path).resolve().relative_to(root.resolve())
    except ValueError:
        return None
    return rel.as_posix()


def _run_git(*args: str, root: Path = REPO) -> str:
    done = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    return done.stdout


# --- guard: PreToolUse (Bash) tripwire -------------------------------------


def _targets_in_bash(command: str) -> list[str]:
    """Best-effort list of paths a Bash command would write.

    Covers redirections, a handful of file-moving verbs, and in-place editors.
    Reading is never reported. Unparseable input yields an empty list, which the
    caller treats as "cannot classify" and lets through.

    A here-document body (``cmd <<'EOF' ... EOF``) is data, not shell, so the
    command is truncated at the first ``<<`` operator before scanning. The
    redirect target of the here-doc line itself is still captured when the line
    both redirects to a file and reads a here-doc (``cat > f <<EOF``), because
    that redirect precedes the ``<<``.
    """
    heredoc_cut = re.search(r"<<-?\s*", command)
    if heredoc_cut:
        # Keep everything up to the here-doc operator; the body after it is the
        # document content, not shell tokens to scan for redirects.
        command = command[: heredoc_cut.start()]
    try:
        words = shlex.split(command)
    except ValueError:
        return []
    targets: list[str] = []
    for i, word in enumerate(words):
        if word in _REDIRECTS and i + 1 < len(words):
            targets.append(words[i + 1])
    head = words[0] if words else ""
    if head in _WRITE_VERBS:
        operands = [w for w in words[1:] if not w.startswith("-")]
        if head in {"cp", "mv", "install"} and len(operands) >= 2:
            targets.append(operands[-1])
        elif head in {"touch", "tee"}:
            targets.extend(operands)
    if head in _INPLACE and _INPLACE[head] in words:
        # For in-place editors the script expression precedes the file; only the
        # trailing operand is a path we should check.
        operands = [w for w in words[1:] if not w.startswith("-")]
        if operands:
            targets.append(operands[-1])
    return targets


def _targets_in_patch(patch_body: str) -> list[str]:
    """Paths an apply_patch body would write, from its file-operation lines."""
    return _PATCH_FILE_LINE.findall(patch_body or "")


def _written_targets(tool_name: str, tool_input: dict) -> list[str]:
    """The paths a write-capable tool call would touch, by tool.

    Returns an empty list for tools that do not write (reads, agent spawns),
    which the caller treats as nothing to police.
    """
    command = tool_input.get("command") or ""
    if tool_name == "apply_patch":
        return _targets_in_patch(command)
    if tool_name == "Bash":
        return _targets_in_bash(command)
    return []


def run_guard(stream=sys.stdin) -> int:
    try:
        payload = json.load(stream)
    except Exception:  # noqa: BLE001 - any failure to read a payload must fail closed
        print("agent-scope: unreadable PreToolUse payload", file=sys.stderr)
        return 2
    role = payload.get("agent_type") or payload.get("agent_role")
    try:
        ledger = ScopeLedger.load()
    except (OSError, ValueError) as err:
        print(f"agent-scope: cannot load policy: {err}", file=sys.stderr)
        return 2
    policy = ledger.policy_for(role)
    if policy is None:
        return 0  # orchestrator or an unscoped built-in agent
    tool_name = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    offenders = []
    for target in _written_targets(tool_name, tool_input):
        rel = _repo_relative(target)
        if rel is None:
            continue  # outside the repository; not ours to police here
        if not policy.permits(rel):
            offenders.append(rel)
    if offenders:
        first = offenders[0]
        print(
            f"agent-scope: the {role} role may not write {first}. "
            f"It is outside the scope authored in workflow/agent-scope/scope.toml. "
            f"Escalate to the orchestrator instead of working around this.",
            file=sys.stderr,
        )
        return 2
    return 0


# --- audit: authoritative diff check ---------------------------------------


def _changed_paths(baseline: str | None, root: Path = REPO) -> list[str]:
    seen: set[str] = set()
    if baseline:
        diff = _run_git("diff", "--name-only", "--no-renames", baseline, root=root)
        seen.update(line for line in diff.splitlines() if line)
    status = _run_git("status", "--porcelain", "--untracked-files=all", root=root)
    for line in status.splitlines():
        if line:
            seen.add(line[3:])
    return sorted(seen)


def run_audit(role: str, baseline: str | None) -> int:
    try:
        ledger = ScopeLedger.load()
    except (OSError, ValueError) as err:
        print(f"agent-scope: cannot load policy: {err}", file=sys.stderr)
        return 2
    policy = ledger.policy_for(role)
    if policy is None:
        print(f"agent-scope: '{role}' is not a scoped role", file=sys.stderr)
        return 2
    strays = [p for p in _changed_paths(baseline) if not policy.permits(p)]
    moved = False
    if baseline:
        head = _run_git("rev-parse", "HEAD").strip()
        moved = head != _run_git("rev-parse", baseline).strip()
    if strays or moved:
        print(f"agent-scope: the {role} role wrote outside its boundary:")
        for path in strays:
            print(f"  {path}")
        if moved:
            print("  HEAD moved: a delegated role must not commit or switch branches")
        return 1
    print(f"agent-scope: every change stays within the {role} boundary.")
    return 0


# --- pin / verify: steady-candidate manifest --------------------------------


def _fingerprint(root: Path = REPO) -> dict:
    listing = _run_git(
        "ls-files", "--cached", "--others", "--exclude-standard", root=root
    )
    digests: dict[str, str] = {}
    for name in sorted(filter(None, listing.splitlines())):
        blob = root / name
        low = blob.name.lower()
        if low == ".env" or (low.startswith(".env.") and low != ".env.example"):
            continue  # never read secrets into a manifest
        if blob.is_file() and not blob.is_symlink():
            digests[name] = hashlib.sha256(blob.read_bytes()).hexdigest()
    head = _run_git("rev-parse", "HEAD").strip()
    return {"schema": 1, "root": str(root.resolve()), "head": head, "digests": digests}


def run_pin(destination: str) -> int:
    out = Path(destination).resolve()
    if _repo_relative(str(out)) is not None:
        print("agent-scope: keep the manifest outside the repository", file=sys.stderr)
        return 2
    out.write_text(json.dumps(_fingerprint(), indent=2) + "\n", encoding="utf-8")
    return 0


def run_verify(manifest: str) -> int:
    before = json.loads(Path(manifest).read_text(encoding="utf-8"))
    after = _fingerprint()
    drift = sorted(
        name
        for name in before["digests"].keys() | after["digests"].keys()
        if before["digests"].get(name) != after["digests"].get(name)
    )
    if before["head"] != after["head"]:
        drift.append("HEAD moved")
    if drift:
        print("agent-scope: the candidate drifted from its pinned manifest:")
        for item in drift:
            print(f"  {item}")
        return 1
    print("agent-scope: candidate matches its pinned manifest.")
    return 0


# --- session-audit: rollout-based post-check -------------------------------
#
# The live guard only sees a write as Codex dispatches it, and only in a client
# that runs PreToolUse hooks. This mode instead reads a finished Codex session
# rollout (the transcript Codex writes under ~/.codex/sessions) and attributes
# every write to the role that made it, independent of client or transport. It
# is the authoritative per-role post-check: a human can read its log and see
# where each role stayed in or stepped outside its lane.


@dataclass(frozen=True)
class ScopeFinding:
    """One out-of-lane write discovered in a rollout."""

    role: str
    path: str
    tool: str
    session_id: str


def _tool_and_input_from_event(event: dict) -> tuple[str, dict] | None:
    """Map a rollout timeline event to guard's (tool_name, tool_input) contract.

    Returns None for events that are not write-capable tool calls. A shell
    command maps to Bash; a custom tool call to its tool name (apply_patch is
    the one that yields paths). Anything else is left for the caller to skip.
    """
    kind = event.get("kind")
    if kind == "cmd":
        command = event.get("command")
        if not isinstance(command, str):
            return None
        return "Bash", {"command": command}
    if kind == "tool":
        tool = event.get("tool")
        command = event.get("command")
        if not isinstance(tool, str) or not isinstance(command, str):
            return None
        # Only apply_patch is a write we can parse from a tool event. Other tool
        # calls (notably the `exec`/`unified_exec` JS wrapper
        # `const r = await tools.exec_command({cmd:"..."})`) are duplicated by a
        # normalized `cmd`-kind event in the same timeline, so processing the raw
        # wrapper here would both double-count and mis-parse stray tokens such as
        # `max_output_tokens:5000`. Skip them; the `cmd` event carries the shell.
        if tool != "apply_patch":
            return None
        return tool, {"command": command}
    return None


def _top_level_repo_entries(root: Path = REPO) -> set[str]:
    """Names of the repository's top-level entries, used to tell a repo-rooted
    path (``backend/app/x.py``) from a subdirectory-relative one (``tests/x.py``
    run from ``backend/``)."""
    try:
        return {p.name for p in root.iterdir()}
    except OSError:
        return set()


def _confidently_repo_rooted(target: str, root: Path = REPO) -> bool:
    """True when a path can be trusted as repo-relative without knowing the cwd.

    The post-check sees commands without a reliable working directory, so a bare
    relative path like ``tests/x.py`` is ambiguous: it may be ``backend/tests/x.py``
    written from ``backend/``. Treat a relative path as repo-rooted only when its
    first segment is an actual top-level repo entry (``backend/...`` is safe;
    ``tests/...`` is not, since this repo has no top-level ``tests``). Absolute
    paths inside the repo are always trusted. Unclassifiable paths are skipped
    rather than flagged, to avoid accusing a correctly-placed write.
    """
    if Path(target).is_absolute():
        return True
    first = Path(target).parts[0] if Path(target).parts else ""
    return first in _top_level_repo_entries(root)


def _findings_for_actor(
    ledger: ScopeLedger,
    role: str | None,
    events: list[dict],
    session_id: str,
) -> list[ScopeFinding]:
    """Out-of-lane writes an actor made, by replaying its timeline events."""
    policy = ledger.policy_for(role)
    if policy is None:
        return []  # orchestrator or an unscoped built-in agent
    findings: list[ScopeFinding] = []
    for event in events:
        mapped = _tool_and_input_from_event(event)
        if mapped is None:
            continue
        tool_name, tool_input = mapped
        for target in _written_targets(tool_name, tool_input):
            if not _confidently_repo_rooted(target):
                continue  # cwd unknown and path not repo-rooted; can't classify
            rel = _repo_relative(target)
            if rel is None:
                continue  # outside the repository; not ours to police
            if not policy.permits(rel):
                findings.append(ScopeFinding(role or "", rel, tool_name, session_id))
    return findings


def audit_rollout_actors(
    actors: list[tuple[str, str | None, list[dict]]],
    ledger: ScopeLedger | None = None,
) -> list[ScopeFinding]:
    """Scope-check a list of (session_id, role, events) actors.

    This is the reusable seam for the eval harness: it already parses rollouts
    into per-actor role + normalized events, so it can hand that structure here
    and surface the findings in its usage report without re-reading the file.
    """
    if ledger is None:
        ledger = ScopeLedger.load()
    findings: list[ScopeFinding] = []
    for session_id, role, events in actors:
        findings.extend(_findings_for_actor(ledger, role, events, session_id))
    return findings


_EXEC_CMD = re.compile(r'tools\.exec_command\(\s*\{\s*cmd\s*:\s*"((?:[^"\\]|\\.)*)"')


def _unwrap_exec_command(raw: str) -> str | None:
    """Pull the shell command out of a `tools.exec_command({cmd:"..."})` call.

    Codex's unified-exec tool arrives as a JS wrapper in the rollout, with the
    real shell command as the quoted `cmd:` value. Returns the decoded command,
    or None if the input is not an exec wrapper.
    """
    match = _EXEC_CMD.search(raw or "")
    if match is None:
        return None
    # The captured group is a JS string literal; decode its escapes.
    try:
        return json.loads(f'"{match.group(1)}"')
    except ValueError:
        return match.group(1)


def _actors_from_rollout(rollout: Path) -> list[tuple[str, str | None, list[dict]]]:
    """Parse one rollout file into (session_id, role, events) standalone.

    A minimal, dependency-free reader so this mode works without the eval
    harness. Each line is a JSON record; we recover the session's role from the
    session_meta payload and the write events from function/custom tool calls.
    Codex encodes shell writes as a `custom_tool_call` named ``exec`` whose
    input wraps the real command in ``tools.exec_command({cmd:"..."})``; those
    are unwrapped to a Bash command. A bare ``apply_patch`` tool call is passed
    through as a patch body.
    """
    session_id = rollout.stem
    role: str | None = None
    events: list[dict] = []
    for line in rollout.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        payload = record.get("payload", record)
        if not isinstance(payload, dict):
            continue
        rtype = record.get("type") or payload.get("type")
        if rtype == "session_meta":
            role = role or payload.get("agent_role") or payload.get("agent_type")
            source = payload.get("source")
            if role is None and isinstance(source, dict):
                spec = source.get("subagent", {}).get("thread_spawn", {})
                role = spec.get("agent_role") or spec.get("agent_type")
            continue
        ptype = payload.get("type")
        if ptype == "custom_tool_call":
            name = payload.get("name")
            raw_input = payload.get("input")
            if not isinstance(raw_input, str):
                continue
            if name == "exec":
                command = _unwrap_exec_command(raw_input)
                if command is not None:
                    events.append({"kind": "cmd", "command": command})
            elif name == "apply_patch":
                events.append(
                    {"kind": "tool", "tool": "apply_patch", "command": raw_input}
                )
        elif ptype in ("local_shell_call", "function_call") and payload.get("name") in (
            "shell",
            "exec",
            "bash",
        ):
            args = payload.get("arguments") or payload.get("action") or ""
            command = _unwrap_exec_command(args) if isinstance(args, str) else None
            if command is None and isinstance(args, str):
                command = args
            if command:
                events.append({"kind": "cmd", "command": command})
    return [(session_id, role, events)]


def run_session_audit(rollout_path: str | None, log_path: str | None) -> int:
    """Scope-check a rollout and record the result.

    Always appends a one-line outcome to the audit log (so a clean run leaves
    positive evidence it ran), and writes a detailed record per violation.
    Exits 1 when any out-of-lane write is found, else 0. Never fails the turn:
    an unreadable rollout is reported and exits 0 so a Stop hook stays quiet.
    """
    import datetime

    log = Path(log_path) if log_path else (HERE / "audit-log.tsv")
    stamp = datetime.datetime.now().isoformat(timespec="seconds")

    if rollout_path:
        rollout = Path(rollout_path)
    else:
        rollout = _latest_rollout()
    if rollout is None or not rollout.is_file():
        print("agent-scope: no rollout to audit", file=sys.stderr)
        return 0

    try:
        actors = _actors_from_rollout(rollout)
        findings = audit_rollout_actors(actors)
    except (OSError, ValueError) as err:
        print(f"agent-scope: cannot audit rollout: {err}", file=sys.stderr)
        return 0

    try:
        with log.open("a", encoding="utf-8") as fh:
            if findings:
                for f in findings:
                    fh.write(
                        f"{stamp}\t{f.session_id}\t{f.role}\tBLOCKED\t{f.tool}\t{f.path}\n"
                    )
            else:
                fh.write(f"{stamp}\t{rollout.stem}\t-\tCLEAN\t-\t-\n")
    except OSError:
        pass

    if findings:
        print(f"agent-scope: {len(findings)} out-of-lane write(s) in {rollout.name}:")
        for f in findings:
            print(f"  {f.role} wrote {f.path} ({f.tool})")
        return 1
    print(f"agent-scope: every write in {rollout.name} stayed within role scope.")
    return 0


def _latest_rollout() -> Path | None:
    """Most-recently-modified Codex rollout under ~/.codex/sessions."""
    root = Path.home() / ".codex" / "sessions"
    if not root.is_dir():
        return None
    rollouts = list(root.rglob("rollout-*.jsonl"))
    if not rollouts:
        return None
    return max(rollouts, key=lambda p: p.stat().st_mtime)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("guard", help="PreToolUse(Bash) tripwire; reads stdin")
    a = modes.add_parser("audit", help="authoritative diff check for a role")
    a.add_argument("role")
    a.add_argument("--baseline", help="commit recorded before the role ran")
    sa = modes.add_parser("session-audit", help="rollout-based per-role post-check")
    sa.add_argument("rollout", nargs="?", help="rollout .jsonl (default: newest)")
    sa.add_argument(
        "--log", help="audit log path (default: audit-log.tsv beside this tool)"
    )
    modes.add_parser("pin", help="record a steady-candidate manifest").add_argument(
        "manifest"
    )
    modes.add_parser(
        "verify", help="confirm a candidate against its manifest"
    ).add_argument("manifest")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    if args.mode == "guard":
        return run_guard()
    if args.mode == "audit":
        return run_audit(args.role, args.baseline)
    if args.mode == "session-audit":
        return run_session_audit(args.rollout, args.log)
    if args.mode == "pin":
        return run_pin(args.manifest)
    if args.mode == "verify":
        return run_verify(args.manifest)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
