# Case provenance

Adapted from the MP3 `implement-task/frontend-quiz-search` case. It keeps the
small quiz-list task and adds an approved, worker-visible prototype plus an
automated browser oracle so the MP4 prototype-reading instruction is exercised.

The worker fixture is isolated. The browser grader uses the MP4 checkout's
installed `frontend` development dependencies and Playwright-managed Chromium.
Before running this case, install frontend dependencies with `npm ci` from
`frontend/` and install the pinned browser with `npm exec -- playwright install chromium`.
