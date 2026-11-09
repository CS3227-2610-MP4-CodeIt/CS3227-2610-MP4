# Complexity catalog — raw HTTP status diagnostic

Generated: 2026-11-09T16:55:53

One minimal chat request per model, straight to POST /v1/chat/completions (bypassing the app client's error swallowing), concurrency capped at 8. Classifies why a model returned non-200 so the model-selection table is fair.

| Model | HTTP status | classification | latency (s) | detail |
| --- | ---: | --- | ---: | --- |
| `llama3.1:8b` | 200 | answered (0/21 = real schema/task failure) | 2.58 |  |
| `nemotron3.5:30b` | 200 | answered (0/21 = real schema/task failure) | 2.02 |  |
| `ornith1.5:35b` | 200 | answered (0/21 = real schema/task failure) | 0.48 |  |
| `qwen3.5:9b` | 200 | answered (0/21 = real schema/task failure) | 1.46 |  |
| `qwen3.6:35b` | 200 | answered (0/21 = real schema/task failure) | 2.12 |  |
| `qwen3.8:27b` | 200 | answered (0/21 = real schema/task failure) | 2.68 |  |
| `qwen3-coder-next` | 200 | answered (0/21 = real schema/task failure) | 2.08 |  |
| `x-test-1` | 200 | answered (0/21 = real schema/task failure) | 2.73 |  |
| `x-test-2` | 200 | answered (0/21 = real schema/task failure) | 2.56 |  |
| `x-test-3` | 200 | answered (0/21 = real schema/task failure) | 1.06 |  |
| `x-test-4` | 200 | answered (0/21 = real schema/task failure) | 0.26 |  |
| `coder` | 200 | answered (0/21 = real schema/task failure) | 15.06 |  |
| `coding` | 200 | answered (0/21 = real schema/task failure) | 26.35 |  |
| `default` | 200 | answered (0/21 = real schema/task failure) | 25.64 |  |
| `ornith1.0:35b` | 200 | answered (0/21 = real schema/task failure) | 27.72 |  |
| `qwen3.6:27b` | 200 | answered (0/21 = real schema/task failure) | 28.27 |  |
| `gemma4:26b` | 503 | provider overloaded (transient) | 0.21 | {"error":"no healthy provider backends for backend group \"79\""}  |
