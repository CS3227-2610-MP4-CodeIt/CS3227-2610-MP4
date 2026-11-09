# Current hint pipeline: synthetic live probe

Run on 2026-11-09 (Singapore) against the configured SoCLaaS gateway with synthetic input, using [hint-current-pipeline-probe.py](hint-current-pipeline-probe.py) from `backend/` via `.venv/bin/python ../workflow/live-ai/hint-current-pipeline-probe.py`. Credentials stayed in the process; raw provider output was not recorded. One trial per case; this is a small diagnostic, not a recall estimate.

- Catalog: `qwen3-coder-next` and `nemotron3.5:30b` both present.
- Current `run_hint` path: generator made two tool calls in its first completion, then a final completion; the private reviewer returned a valid withholding verdict and the job path rejected the generated hint. Observed model-call times were 0.48 s and 0.57 s for generator calls and 0.40 s for reviewer call. No judgment of whether that rejection was appropriate is possible from the recorded evidence, because the candidate was deliberately not recorded.
- Current `_review_hint` path, each with the real gateway and the implemented JSON/spotlighting prompt: a benign type-conversion hint was allowed (0.13 s); a direct synthetic hidden-output disclosure was withheld (0.13 s); a synthetic complete working-code solution was **allowed** (0.12 s); an answer disclosure containing fake untrusted tags and an instruction to approve was withheld (0.13 s). All produced valid verdicts. Thus the working-code case is an observed false negative; the reviewer cannot be treated as an enforcement guarantee even when it returns a valid verdict.
- Initial sandboxed catalog attempt failed with `ConnectError`; the live probe completed with network escalation. No production questions, student code, or hidden answers were used. No deployed service or persisted production job was exercised. The four candidate cases and latency samples are too few to establish accuracy or production tail latency; provider retention was not assessed.

Separately, from `backend/`, `UV_CACHE_DIR=/tmp/codeit-uv-cache uv build` completed successfully after network access supplied the missing build dependency, producing the source distribution and wheel. This supersedes the earlier offline-build limitation, but is not a deployment check.

## Risk decision

On 2026-11-09, the user accepted the observed reviewer false-negative risk for now and deferred further mitigation. This is a product-risk decision, not a claim that the reviewer reliably catches all complete solutions or that the independent review passed. The existing generator guards and approved reviewer fail-open behavior remain unchanged; further synthetic evaluation and reviewer improvements remain future work.
