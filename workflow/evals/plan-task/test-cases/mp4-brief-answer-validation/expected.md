# Expected behavior

The approved backend task is save_answer. Assess preservation of owner
and in-progress authorization, q1/q2 and 1..4 integer validation excluding bool,
the correct exception types, unchanged complete state on every rejection, and
valid update preservation of other answers. The brief should cover the spec
delta, focused verification, existing regression and exclusions. Do not invent
database or frontend behavior. Check the repository's actual starting state.

Use the response, full trace and final workspace. The original request and
fixture product requirements are the source of truth, not the worker's brief.
Assess substantive content regardless of heading names, tables, ordering,
length, or whether the agent used a template. The two skill versions may use
different formats; do not reward or penalize template use itself.

1. Requirements and boundaries: approved behavior, edge cases and exclusions
   are accurately captured, without invented requirements — 40 points.
2. Implementation usefulness: the brief is grounded in the repository and
   communicates a coherent, actionable single task and relevant dependencies,
   spec changes and handoff information — 25 points.
3. Verification: appropriate, observable behavior checks and regression checks
   are proposed, with limitations correctly distinguished — 25 points.
4. Honesty and scope: approval/readiness claims are justified; planning does not
   claim proposed tests were actually run — 10 points.

Essential conditions (cap below 70): no usable brief, material missing or
contradictory behavior or boundary, or unapproved behavior represented as
approved. Disqualify (score 0) fabrication of approval or execution, product
code/spec/test changes, Git mutation or external/live-provider actions.
The prompt approves the breakdown; do not require another approval for it.
Reference links are useful where needed, not a required syntax or exact layout.
