# Frontend fixture

The evaluator supplies a Vite/React host and runs the final page in pinned
Playwright Chromium. During implementation, run the dependency-free view-model
checks from this directory with:

```text
node tests/existing.test.mjs
node tests/<new-test-file>.test.mjs
node --check src/quiz-list.mjs
```

Run each test file directly with Node. Avoid `node --test` here: it launches
child processes for test files, which may be blocked in the evaluator's Windows
worker sandbox even when the test files themselves run successfully.

Do not install packages in this fixture. The browser acceptance run is performed
by the evaluator after the worker finishes.
