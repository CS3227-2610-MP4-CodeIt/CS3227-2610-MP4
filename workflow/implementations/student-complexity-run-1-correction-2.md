# Student complexity correction 2

Status: IMPLEMENTED; independent review remains outstanding. Task: [brief](../tasks/student-code-complexity-analysis.md); assigned review: [run 2](../reviews/student-complexity-run-2.md).

Baseline HEAD `07ba2c4ca8963133d431359cb04f65ab724e840e`; pre-existing task implementation, task/review artifacts, agent-scope and evaluation changes were preserved. Review target is HEAD plus the 16 task paths in the correction-1 handoff; aggregate SHA-256 of their ordered per-file SHA-256 listing is `8652ec0b2f82a71e5d001f34b4e5265e0d046e62cb1cb244f93c3a01ca1334f6`. No commit.

`SC-complexity-1`: moved the existing complexity contract to §7.5 under “Features using jobs,” corrected the student endpoint table reference to §7.5, and included complexity code in the prompt-guard input description. The contract itself is unchanged. Changed path: [backend specification](../../specs/backend-spec.md). Acceptance criterion 7 is addressed; no behavior or tests changed.

Verification, executor implementation agent, repository root: `rg -n '^## 7\.|^### 7\.|^## 8\.|^## 13\.|complexity.*§7.5|student code \(hints' specs/backend-spec.md` showed §7.5 within §7, the endpoint reference, and §13 separately; `git diff --check` passed. Source inspection of the scoped diff confirmed the moved text and cross-reference. No automated tests were run for this documentation-only correction.

Remaining review evidence limitations are unchanged: real-backend browser integration and independently reproduced packaging were not assessed in this correction; no live model or deployment check. Review must reassess the corrected target. No other finding was assigned.
