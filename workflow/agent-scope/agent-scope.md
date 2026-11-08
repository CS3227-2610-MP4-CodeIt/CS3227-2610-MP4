# Agent write-scope enforcement

This folder keeps each delegated Codex agent inside the file boundary a human
authored, so that a role cannot quietly edit another role's output or the
project's secrets. The boundary is policy (`scope.toml`), the enforcer is a
small tool (`guard.py`), and the enforcement runs at two points with different
strengths.

## Why two points

CodeIt runs one writing agent (`task_implementer`) and a read-only review panel
(`code_quality_reviewer`, `spec_contract_reviewer`, `security_boundary_reviewer`,
`verification_reviewer`, `review_aggregator`). The intended rule is simple: the
panel writes only its findings under `workflow/reviews/`, and the implementer
writes product code but never the panel's artifacts, the planner's task briefs,
or any `.env`. That rule used to live only in the agent prompts, which is a
request, not a control.

Codex's `PreToolUse` hook observes **Bash commands only**; it does not see an
`apply_patch` edit. So a live hook can be a useful tripwire for shell writes, but
it is not a complete boundary on its own. The honest design is therefore:

- a **live guard** on `PreToolUse(Bash)` that refuses an out-of-scope shell
  write immediately, and
- an **authoritative audit** the orchestrator runs against the diff after a role
  returns, which catches every write regardless of how it was made.

The audit is the real acceptance check. The guard is a fast warning for the
vector Codex exposes.

## The policy — `scope.toml`

Each role has an `allow` list and a `block` list of repository-relative glob
patterns (`fnmatch` semantics, `*` spans `/`). A write is permitted when it
matches some `allow` pattern and no `block` pattern; `block` always wins. An
unknown role (the orchestrator, a built-in agent) is unrestricted; an empty
`allow` forbids every write.

The policy is authored by a human and is the artifact to review for correctness.
The two properties that matter: the per-role lists are meaningful (a role can
reach what its task needs) and they do not overlap in a way that defeats the
separation (e.g. the implementer must not be able to reach `workflow/reviews/`).

`scope.toml` is **not** read by Codex and adds no keys to `.codex/config.toml`.

## Running it

From the repository root (Python 3.11+, standard library only):

```sh
# Live guard — normally invoked by the PreToolUse(Bash) hook, not by hand.
echo '{"agent_type":"code_quality_reviewer","tool_input":{"command":"echo x > backend/app/main.py"}}' \
  | python3 workflow/agent-scope/guard.py guard        # exits 2, prints the refusal

# Authoritative audit — run after a delegated role finishes.
git rev-parse HEAD                                       # record this before dispatching the role
python3 workflow/agent-scope/guard.py audit task_implementer --baseline <that-commit>

# Steady a review candidate across a review pass.
python3 workflow/agent-scope/guard.py pin   /tmp/codeit-candidate.json   # outside the repo
python3 workflow/agent-scope/guard.py verify /tmp/codeit-candidate.json

# Tests.
python3 -m pytest workflow/agent-scope/tests -q
```

## How it is wired

`.codex/hooks.json` registers the guard under `PreToolUse` with the `Bash`
matcher, alongside the existing `Stop` telemetry hook. Both commands resolve
their path with `git rev-parse --show-toplevel` so they work from any
subdirectory. The guard exits 2 to block; Codex treats exit 2 as a refusal and
returns the stderr message to the agent.

## The human's part

This control exists to relocate judgment to a person, not to remove it:

- A human **authors** `scope.toml` from the project's module boundaries. The
  agent cannot write its own scope.
- When a role legitimately needs a path outside its lane, the guard stops it and
  it must **escalate to the orchestrator**, who decides: widen the policy, make
  the shared edit directly, or reassign. Those escalations are the record of
  where human judgment entered.
- The orchestrator runs the **audit** and keeps its output as evidence that the
  boundary held.

## Honest limits

- `PreToolUse` in Codex sees Bash only. `apply_patch` edits are not blocked live;
  the diff audit is what catches them. Do not describe the guard as a complete
  real-time boundary.
- The guarantee depends on the policy's `allow`/`block` lists being correct and
  appropriately disjoint. A bad policy is enforced faithfully — the tool does not
  judge the policy.
- The guard keys on the role identity in the hook payload (`agent_type`, or
  `agent_role`). If a Codex version does not supply a role on the payload, the
  guard cannot scope that call and lets it through; the audit still applies.
- This is a development-workflow coordination control. It is not a security
  boundary for untrusted student code — that lives in the code-execution
  sandbox.
