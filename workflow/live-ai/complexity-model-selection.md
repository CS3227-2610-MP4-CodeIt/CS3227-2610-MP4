# Complexity feature — live model selection

Generated: 2026-11-09T17:15:34

Ran CodeIt's real complexity pipeline (prompt + guards + ComplexityResult schema) across the live SoCLaaS catalog on 7 known-answer fixtures, 3 trials each (21 calls per model). `format-valid` = reply passed canary + size + JSON schema (exactly what the app accepts). `time`/`space` = Big-O matched the known answer. Evidence over a fixed fixture set, not proof on unseen code.

| Model | format-valid | time correct | space correct | median latency (s) |
| --- | ---: | ---: | ---: | ---: |
| `ornith1.5:35b` | 17/21 | 17/21 | 17/21 | 5.9 |
| `ornith1.0:35b` | 16/21 | 16/21 | 16/21 | 6.87 |
| `x-test-2` | 14/21 | 14/21 | 14/21 | 10.01 |
| `qwen3.6:35b` | 11/21 | 11/21 | 11/21 | 5.01 |
| `x-test-4` | 11/21 | 11/21 | 11/21 | 5.15 |
| `x-test-3` | 11/21 | 11/21 | 11/21 | 25.47 |
| `llama3.1:8b` | 5/21 | 5/21 | 5/21 | 3.31 |
| `default` | 4/21 | 4/21 | 4/21 | 36.26 |
| `x-test-1` | 2/21 | 2/21 | 2/21 | 28.38 |
| `qwen3-coder-next` | 1/21 | 1/21 | 1/21 | 23.3 |
| `nemotron3.5:30b` | 0/21 | 0/21 | 0/21 | 1.2 |
| `gemma4:26b` | 0/21 | 0/21 | 0/21 | 7.32 |
| `qwen3.5:9b` | 0/21 | 0/21 | 0/21 | 45.0 |
| `qwen3.8:27b` | 0/21 | 0/21 | 0/21 | 45.06 |
| `coding` | 0/21 | 0/21 | 0/21 | 45.07 |
| `qwen3.6:27b` | 0/21 | 0/21 | 0/21 | 45.07 |
| `coder` | 0/21 | 0/21 | 0/21 | 45.08 |

## Failure reasons per model

- `ornith1.5:35b`: invalid_schema_or_json×4
- `ornith1.0:35b`: invalid_schema_or_json×5
- `x-test-2`: invalid_schema_or_json×7
- `qwen3.6:35b`: invalid_schema_or_json×10
- `x-test-4`: invalid_schema_or_json×10
- `x-test-3`: call_error:UserFacingError×2, invalid_schema_or_json×8
- `llama3.1:8b`: invalid_schema_or_json×16
- `default`: call_error:UserFacingError×16, invalid_schema_or_json×1
- `x-test-1`: invalid_schema_or_json×19
- `qwen3-coder-next`: call_error:UserFacingError×9, invalid_schema_or_json×11
- `nemotron3.5:30b`: invalid_schema_or_json×21
- `gemma4:26b`: call_error:UserFacingError×21
- `qwen3.5:9b`: call_error:UserFacingError×11, invalid_schema_or_json×10
- `qwen3.8:27b`: call_error:UserFacingError×21
- `coding`: call_error:UserFacingError×21
- `qwen3.6:27b`: call_error:UserFacingError×21
- `coder`: call_error:UserFacingError×20, invalid_schema_or_json×1

## Reading the failure reasons

`call_error:UserFacingError` is the app client's single error type for every
non-200 response — it does not distinguish 429 / 400 / 503 / timeout. A separate
raw-status diagnostic (`model-status-diagnostic.md`, one minimal call per model at
concurrency 8) showed **16 of 17 models return HTTP 200** and are fully
chat-eligible; only `gemma4:26b` was transiently 503. So:

- The `call_error×21` rows at ~45 s median (`qwen3.8:27b`, `coding`,
  `qwen3.6:27b`, `coder`) are **timeouts** — the model is eligible but too slow
  to answer within the 45 s chat timeout, not rate-limited and not ineligible.
- `gemma4:26b` was a transient 503.
- `invalid_schema_or_json` is a **real task failure**: the model answered but its
  JSON did not satisfy `ComplexityResult` (e.g. `assumptions` as an array, extra
  keys, or prose outside the JSON object).

An earlier run at concurrency 16 showed many of these models at 0/21 with
`call_error×21` around ~7 s — that was **429 rate-limiting from our own
concurrency**, not the models failing the task. Re-running at concurrency 8 gave
them a fair shot (e.g. `x-test-2` went 0/21 → 14/21). The table above is the
concurrency-8 result.

## Selection

- **Primary: `ornith1.5:35b`** — 17/21 valid, all 17 correct on both time and
  space, 5.9 s median. Highest accuracy with competitive latency.
- **Fallback: `ornith1.0:35b`** — 16/21, 6.87 s median.
- The currently-configured models are unusable or weak for this feature:
  `.env` `LLM_MODEL=x-test-4` lands at 11/21 and the `config.py` default `coder`
  times out (0/21). Complexity needs its own model wired to `ornith1.5:35b`.
