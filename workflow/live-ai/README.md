# Live AI testing (SoCLaaS)

Opt-in, manually-run probes that exercise CodeIt's AI features against the **real**
SoCLaaS provider. These are **not** part of CI: the deterministic/mocked contract
tests in `backend/tests/` cover the simulated contract; these probes cover what
mocks cannot — whether the live model returns usable, safe output through the
app's real prompt, guards, and validation.

Two angles, per the [live-SoCLaaS peer survey](../../CS3227-Planning/...):
- **Reliability** — given legitimate input, does the model produce output the
  product accepts (correct schema, usable content)?
- **Security** — given adversarial input, does the boundary hold (no canary leak,
  correct refusal)?

Model selection is **per feature** — a model that is best for one feature may not
be best for another. Each feature's probe runs the real pipeline across the live
model catalog and reports format-validity, latency, and answer-correctness.

## Running

Requires `backend/.env` with `SOCLAAS_BASE_URL` and `SOCLAAS_API_KEY`, and the
backend venv (Python 3.14). From `backend/`:

```sh
.venv/bin/python ../workflow/live-ai/complexity_model_selection.py
```

The script makes real API calls. It writes a results table to
`workflow/live-ai/complexity-model-selection.md`. It never stores API keys or raw
model text beyond bounded, redacted snippets.

## Files

- `complexity_model_selection.py` — model-selection probe for the complexity
  feature. Runs the real complexity pipeline (prompt + guards + schema) across
  catalog models on known-answer fixtures.
- `complexity_fixtures.py` — Python snippets with known Big-O time/space answers.
- `complexity-model-selection.md` — latest results (regenerated each run).
