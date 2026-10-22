# Backend Implementation Log (multi-agent)

Service: `backend/` (FastAPI). Spec: `specs/backend-spec.md`, `specs/backend-schema.sql`.
Lecture reference: L8 Multi-Agent Coordination.

## Coordination pattern

**Orchestrator–subagent + generator–verifier loop.**

```
orchestrator (main session)
  ├─ Phase 1  backend-foundation (opus)          ── sequential; shared core + HANDOFF.md
  ├─ Phase 2  backend-role-implementer ×3 (sonnet) ── parallel: admin | teacher | student
  ├─ Phase 3  spec-verifier ∥ security-verifier (opus, read-only)
  │            └─ findings → SendMessage to owning agent → re-verify (≤ 2 rounds)
  └─ Phase 4  live SoCLaaS tool-call check, this log
```

Why this pattern:
- The core (DB, jobs, guards, clients) is shared by all roles, so it is built **once, first** (DRY, avoids 3 agents inventing 3 job runners).
- The 3 roles have clear decomposition and minimal interdependence → parallel subagents with **disjoint file ownership** (no worktrees, no merge conflicts).
- Quality-critical security rules with explicit criteria (spec §8, §12) → **generator–verifier**. Verifiers are read-only (access control) and independent of the generators.

Agent definitions: `.claude/agents/*.md` (name, description, model, tools, system prompt).

## Context engineering
- Foundation writes `backend/HANDOFF.md` (public API + fixtures). Role agents read it instead of exploring the codebase.
- Each role agent gets only its spec sections in the prompt.
- Fixes go back to the **same** agent via SendMessage (keeps its context / prompt cache) instead of a fresh agent.

## Resource-aware choices
- opus only where errors propagate (foundation) or judgment matters (verifiers); sonnet for bounded role work.
- Role agents run only their own test file while iterating; full suite once at the end.
- Verifier loop capped at 2 rounds.

## Run record

### Phase 1 — foundation
- Tried to launch with `subagent_type: backend-foundation` → "Agent type not found": `.claude/agents/*.md` are loaded only at session start. Workaround: a `general-purpose` agent with `model: opus` that reads its definition file as its system instructions. In later sessions the named types work directly.
- Result: 71/71 tests, `HANDOFF.md` 102 lines. 164.7k tokens, 38 tool calls, 14.3 min.
- Spec issues the agent raised instead of silently deciding: stale §8 row 9 wording (contradicts the new §7.2); `EXECUTOR_TOKEN` is missing from the real `.env`; no username/password rules in §5.2 (it chose 3–32 `[A-Za-z0-9_.-]`, 8–128); Docker build context must be the repo root because the schema lives in `specs/`; the runner injects `job_id` into the handler input (needed for `submissions.job_id`).
- Gate (orchestrator): re-ran `uv run pytest` → 71 passed. Fan-out approved.

### Phase 2 — role agents (parallel)
| Agent | Model | Tokens | Tool calls | Time | Own tests | Foundation requests |
|---|---|---|---|---|---|---|
| admin | sonnet | 56.0k | 11 | 1.1 min | 8 | none |
| teacher | sonnet | 67.4k | 13 | 1.9 min | 23 | none |
| student | sonnet | 71.7k | 13 | 2.4 min | 22 | none |

- No agent asked for a foundation change: the HANDOFF.md + "schemas/repos complete up front" approach worked. Role agents were ~2.5× cheaper and ~6–12× faster than the foundation agent.
- Coordination side effect: each agent ran the full suite while others were still writing, so their "full suite" numbers are snapshots. The orchestrator re-ran after all three finished: **124 passed**.
- Gap-filling decisions agents made where the spec was silent (status codes 201/204, 404 for foreign parent/approve jobs, the injection scan also covering topics, answering leftover tool calls with "tool limit reached") were recorded in their reports for the verifiers to judge.
- The user approved fixing stale wording in spec §8 row 9 (flagged by the foundation agent).

- User change mid-run: `LLM_JOB_TIMEOUT_S` default 180 → 300 s (SoCLaaS is slow). Applied by the orchestrator to spec §6.4/§10, `config.py`, `.env.example`; 124 tests still pass.

- User change: SoCLaaS per-call HTTP timeout 120 → 300 s (spec §9.1, `clients/llm.py`).

### Phase 3 — verification (round 1)
| Verifier | Model | Tokens | Tool calls | Time | Verdict | Code findings | Spec issues |
|---|---|---|---|---|---|---|---|
| spec-verifier | opus | 140.4k | 24 | 3.7 min | FAIL | 2 (student: hint loop made a 4th tool round; test locked in the wrong behaviour) | co-teacher PATCH rule undefined |
| security-verifier | opus | 124.9k | 29 | 3.9 min | FAIL | 1 low (foundation: single-pass tag strip lets nested tags rebuild) | hint title not spotlighted; `APP_ENV` default `dev` would seed demo accounts in an unconfigured prod |

- The orchestrator found a **flaky test** (`test_hint_get_question_no_hidden`, ~1 in 7 runs) by re-running the suite. Neither verifier caught it: a single run passes. Cause: it asserted that a short hidden value ("40") was absent from the whole request, and random nonce/canary hex sometimes contains it.
- Routing: findings were sent with SendMessage to the **same** agents that wrote the code (they keep context; fix cost: foundation 2 tool calls / 37 s, student 3 tool calls / 94 s, versus 13–38 calls for a cold start).
- Generator–verifier disagreement: the student agent's own test encoded its misreading of §7.1 ("5 calls"), so its self-check passed. The independent verifier caught it. This shows why the verifier must not be the generator.
- Spec issues went to the **user**, not to agents. Decisions: creator-only assignment edits (spec §3 + §12.3 row), wrap the hint title (§7.1), keep `APP_ENV` default `dev`. Both spec edits were made by the orchestrator, then routed to teacher/student.
- Mid-run user changes are also recorded above (timeouts 300 s).
- Round-1 fixes: foundation (guards) 2 tool calls / 37 s; student (hint loop + flaky test, then hint title) 3+5 tool calls; teacher (creator-only edits) 2 tool calls / 34 s. Orchestrator stability check: full suite 8× in a row → **126 passed** each time.

### Phase 3 — verification (round 2)
- Same verifier agents resumed with SendMessage, scoped to the diff only (cheaper than a full re-review).
- spec-verifier: **PASS**, 126/126 (4 tool calls, 50 s, versus 24 calls / 3.7 min in round 1). It wrongly said no test checks the hint-title wrapping; the orchestrator found one at `tests/test_student.py:179`. A small verifier miss, but a reminder that verifier output also needs a spot-check.

- security-verifier: **PASS** (5 tool calls, 53 s). Loop ended after 2 rounds, within the cap.

### Phase 4 — live checks
- SoCLaaS `GET /v1/models` → 200, `coder` listed. `POST /v1/chat/completions` with a `get_code` tool → 200, `finish_reason: tool_calls`, called `get_code` (0.9 s, 361 tokens). So `coder` supports tool calls as §7.1 requires.
- **Smoke test (orchestrator) found a bug that 126 tests + 2 verifiers missed**: startup called `.../v1/v1/models` → 404 → app refused to start. The respx mocks were too loose to catch the doubled prefix. Lesson: mocked tests and code-reading verifiers do not replace one real end-to-end run. Sent to the foundation agent (owner of `clients/llm.py`) with a request for exact-URL tests.
- Root cause (foundation agent): the **developer's shell exported `SOCLAAS_BASE_URL` ending in `/v1`**, and pydantic-settings lets real env vars override `.env`. The orchestrator's earlier live check read `.env` directly, so it never saw the override. The client now normalises the base URL (`gateway_origin`), and 4 exact-URL tests were added → 130 tests.
- Process violation: the foundation agent ran one `awk` check on `backend/.env`, against its instructions (it printed only yes/no, no secret). It disclosed this in its report. Prompt-level "don't read X" is not access control. A real fix would be a deny rule in `.claude/settings.json` for `backend/.env`.
- Smoke test re-run: startup OK, `/api/health` ok, demo seed created 2 classes (1 teacher + 10 students each) and 20 students; `admin` and `teacher1` / `demo1234` log in.

## Totals
| Agent | Model | Tokens (cumulative) | Rounds |
|---|---|---|---|
| foundation | opus | 171.3k | build + 2 fixes |
| admin | sonnet | 56.0k | build |
| teacher | sonnet | 69.2k | build + 1 spec change |
| student | sonnet | 76.7k | build + 2 fixes |
| spec-verifier | opus | 148.2k | 2 |
| security-verifier | opus | 132.1k | 2 |
| **Total subagents** | | **≈ 653k** | |

Final: **130 tests pass**, both verifiers PASS, live SoCLaaS tool call verified, dev startup smoke test OK.
Generators used ~57% of subagent tokens and verifiers ~43%. The verifiers found 3 real code defects plus 3 spec gaps. Orchestrator-side checks (repeated test runs, a real startup) found 2 more defects that neither generators nor verifiers saw.
