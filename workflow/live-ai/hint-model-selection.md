# Hint feature — live model selection (deterministic signals)

Generated: 2026-11-09T20:15:37

Real hint pipeline (prompt + get_question/get_code tool loop + guards) across the live catalog, 5 fixtures × 2 trials (10 runs per model). Hint quality is judged by a human from `hint-model-selection-outputs.md`; this table is only the mechanical signals. `produced` = non-empty, canary-clean hint. `over_code` = more than 5 lines of fenced code (violates the feature rule). `answer_leak` = hidden expected output appeared verbatim. `solution_leak` = the full reference solution appeared.

| Model | produced | over_code | answer_leak | solution_leak | canary_leak | errors | median s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `nemotron3.5:30b` | 10/10 | 0 | 0 | 0 | 0 | 0 | 1.5 |
| `qwen3-coder-next` | 10/10 | 0 | 0 | 0 | 0 | 0 | 2.37 |
| `qwen3.6:35b` | 10/10 | 1 | 0 | 0 | 0 | 0 | 3.45 |
| `ornith1.5:35b` | 10/10 | 1 | 0 | 0 | 0 | 0 | 3.87 |
| `x-test-4` | 10/10 | 0 | 0 | 0 | 0 | 0 | 3.89 |
| `llama3.1:8b` | 10/10 | 1 | 0 | 0 | 0 | 0 | 4.72 |
| `default` | 10/10 | 0 | 0 | 0 | 0 | 0 | 7.04 |
| `ornith1.0:35b` | 10/10 | 1 | 0 | 0 | 0 | 0 | 8.28 |
| `x-test-3` | 10/10 | 0 | 0 | 0 | 0 | 0 | 8.88 |
| `x-test-2` | 10/10 | 0 | 0 | 0 | 0 | 0 | 11.38 |
| `coder` | 9/10 | 0 | 0 | 0 | 0 | 1 | 11.54 |
| `qwen3.6:27b` | 9/10 | 0 | 0 | 0 | 0 | 1 | 26.73 |
| `qwen3.8:27b` | 7/10 | 0 | 0 | 0 | 0 | 3 | 48.82 |
| `qwen3.5:9b` | 6/10 | 0 | 0 | 0 | 0 | 0 | 26.94 |
| `coding` | 2/10 | 0 | 0 | 0 | 0 | 8 | 65.17 |
| `gemma4:26b` | 0/10 | 0 | 0 | 0 | 0 | 10 | 7.62 |
| `x-test-1` | 0/10 | 0 | 0 | 0 | 0 | 10 | 61.29 |
