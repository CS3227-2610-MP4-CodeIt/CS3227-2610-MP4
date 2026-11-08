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
    """
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
    listing = _run_git("ls-files", "--cached", "--others", "--exclude-standard", root=root)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("guard", help="PreToolUse(Bash) tripwire; reads stdin")
    a = modes.add_parser("audit", help="authoritative diff check for a role")
    a.add_argument("role")
    a.add_argument("--baseline", help="commit recorded before the role ran")
    modes.add_parser("pin", help="record a steady-candidate manifest").add_argument("manifest")
    modes.add_parser("verify", help="confirm a candidate against its manifest").add_argument(
        "manifest"
    )
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    if args.mode == "guard":
        return run_guard()
    if args.mode == "audit":
        return run_audit(args.role, args.baseline)
    if args.mode == "pin":
        return run_pin(args.manifest)
    if args.mode == "verify":
        return run_verify(args.manifest)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
