# CodeIt repository guidance

## Project

CodeIt is a secured, AI-assisted programming coursework platform. The repository has a React/Vite frontend, a FastAPI backend, and an isolated Python code-execution service. It is a CS3227 MP4 team project with multiple roles and a specialized-agent development workflow.

## Sources of truth

- Follow the assignment constraints in `assignment-brief.md`.
- Use `specs/` for product behavior and service contracts. Read the relevant backend, frontend, or code-execution spec before changing that area.
- Treat explicit user instructions and the task or review artifacts assigned for the current work as current direction. Where they conflict with a specification or each other, surface the conflict before making a consequential assumption.
- Treat logs, evaluation reports, old plans, and other historical workflow records as evidence about past work, not as current requirements. They must not override current instructions or specifications.
- Component READMEs describe local setup and commands. Check the relevant README before running a service or its checks.

## Repository layout

- `backend/`: FastAPI API, persistence, authentication, AI features, and backend tests.
- `code-execution/`: Python submission judge and its tests. Its tests rely on Linux resource limits; run them on Linux or in the configured Docker/CI environment.
- `frontend/`: React, TypeScript, and Vite application for students, teachers, and admins.
- `specs/`: product and service requirements.
- `workflow/`: task, review, security, evaluation, and development-process artifacts.
- `docs/`: user and developer guides and reflections.
- `.agents/skills/`: reusable workflow and review skills.
- `.codex/agents/` and `.codex/config.toml`: named Codex agent profiles and registrations.

## Change and documentation guidance

- Keep changes within the requested scope and preserve existing contracts and security boundaries.
- Update specifications or acceptance tests when an approved behavior change requires it. Do not update general product documentation for every code change; update `docs/` when requested or when the task includes a documentation change needed to keep user-facing or submission information accurate.
- When relevant, use the project skill that matches the assigned task or review. The current workflow skills are under `.agents/skills/`; do not assume a historical report describes the current workflow.
- Do not claim a check passed unless it was run. Report the commands run and any environmental limitation.

## Local verification

Use the commands documented in the component README. Common checks are:

- Backend, from `backend/`: `uv sync --locked`, `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy app`, `uv run pytest -q`, and `uv build`.
- Code execution, from `code-execution/` on Linux: the same Ruff, mypy, pytest, and build checks documented in its README/CI workflow.
- Frontend, from `frontend/`: `npm ci`, `npm run format:check`, `npm run lint`, `npm test`, and `npm run build`.
- Security scan, from repository root: follow `workflow/security/semgrep.md` and invoke `sh workflow/security/semgrep.sh` with the documented Semgrep setup.

The GitHub Actions workflows under `.github/workflows/` are the authoritative automated check definitions. Run only checks relevant to the change when practical, and state clearly which were run.

## Security and product constraints

- Keep secrets, local environment files, credentials, and private data out of source control and logs. Never print or copy values from `.env` files.
- Preserve backend authorization and resource ownership checks; frontend restrictions alone are not security controls.
- Keep untrusted student code inside the isolated code-execution boundary. Do not weaken its sandbox or expose judge-only test data through student-facing responses.
- Route AI behavior through the documented backend integration and preserve prompt/data separation, validation, and resource limits specified in `specs/`.
- Production deployment must remain team-managed and separate from development, as required by `assignment-brief.md`.
