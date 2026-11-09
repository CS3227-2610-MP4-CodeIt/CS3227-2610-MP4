# Complexity feature — round 2: prompt-technique A/B

Generated: 2026-11-09T18:23:23

Three model classes × 6 prompt variants × 7 known-answer fixtures × 3 trials (21 calls per cell). Identical guards wrapper, canary, and ComplexityResult schema as the real pipeline; the system prompt (and, for V5, the JSON parser) is the only variable. `valid` = passed canary + size + schema. `time`/`space` = Big-O matched the known answer.

## Format-valid rate (valid / 21) by model × variant

| Variant | `ornith1.5:35b` | `x-test-2` | `qwen3.6:35b` |
| --- | ---: | ---: | ---: |
| V0 zero-shot-baseline | 15/21 | 11/21 | 8/21 |
| V1 zero-shot-format | 15/21 | 13/21 | 19/21 |
| V2 few-shot | 20/21 | 16/21 | 21/21 |
| V3 chain-of-thought | 18/21 | 11/21 | 17/21 |
| V4 role-persona | 18/21 | 11/21 | 15/21 |
| V5 lenient-parse | 14/21 | 7/21 | 20/21 |

## Correct Big-O (time+space both correct, / 21) by model × variant

| Variant | `ornith1.5:35b` | `x-test-2` | `qwen3.6:35b` |
| --- | ---: | ---: | ---: |
| V0 zero-shot-baseline | 15/21 | 11/21 | 8/21 |
| V1 zero-shot-format | 15/21 | 13/21 | 19/21 |
| V2 few-shot | 20/21 | 16/21 | 21/21 |
| V3 chain-of-thought | 17/21 | 11/21 | 17/21 |
| V4 role-persona | 18/21 | 11/21 | 15/21 |
| V5 lenient-parse | 14/21 | 7/21 | 20/21 |

## Median latency (s) by model × variant

| Variant | `ornith1.5:35b` | `x-test-2` | `qwen3.6:35b` |
| --- | ---: | ---: | ---: |
| V0 zero-shot-baseline | 10.52 | 4.31 | 4.73 |
| V1 zero-shot-format | 7.0 | 5.55 | 3.77 |
| V2 few-shot | 6.36 | 4.31 | 3.55 |
| V3 chain-of-thought | 9.44 | 5.2 | 4.36 |
| V4 role-persona | 6.48 | 4.91 | 3.76 |
| V5 lenient-parse | 8.1 | 6.18 | 3.81 |

## Failure reasons per cell

- `ornith1.5:35b` / V0 zero-shot-baseline: invalid_schema_or_json×6
- `x-test-2` / V0 zero-shot-baseline: invalid_schema_or_json×10
- `qwen3.6:35b` / V0 zero-shot-baseline: invalid_schema_or_json×13
- `ornith1.5:35b` / V1 zero-shot-format: invalid_schema_or_json×6
- `x-test-2` / V1 zero-shot-format: invalid_schema_or_json×8
- `qwen3.6:35b` / V1 zero-shot-format: invalid_schema_or_json×2
- `ornith1.5:35b` / V2 few-shot: invalid_schema_or_json×1
- `x-test-2` / V2 few-shot: invalid_schema_or_json×5
- `ornith1.5:35b` / V3 chain-of-thought: call_error:UserFacingError×1, invalid_schema_or_json×2
- `x-test-2` / V3 chain-of-thought: invalid_schema_or_json×10
- `qwen3.6:35b` / V3 chain-of-thought: invalid_schema_or_json×4
- `ornith1.5:35b` / V4 role-persona: invalid_schema_or_json×3
- `x-test-2` / V4 role-persona: invalid_schema_or_json×10
- `qwen3.6:35b` / V4 role-persona: invalid_schema_or_json×6
- `ornith1.5:35b` / V5 lenient-parse: invalid_schema_or_json×7
- `x-test-2` / V5 lenient-parse: invalid_schema_or_json×14
- `qwen3.6:35b` / V5 lenient-parse: invalid_schema_or_json×1
