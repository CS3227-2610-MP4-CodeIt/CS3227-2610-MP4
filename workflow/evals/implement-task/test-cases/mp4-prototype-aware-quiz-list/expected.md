# Expected behavior

Judge the whole worker run from its final files, tests, trace, handoff, Git
evidence, and `browser_observations` in `grades/deterministic/result.json`.
The deterministic checker only captures evidence; its score does not represent
the implementation's quality. Use judgment across the criteria below. Do not
require a particular component tree, CSS class, file name, or control label
unless the product contract fixes it.

1. **Test-first work and regression coverage — 30 points.** Focused tests cover
   the new search behavior and preserve the existing status/order regression.
   Prefer trace evidence of a meaningful failing behavior assertion before the
   implementation and passing checks afterward. A setup/import error alone is
   not a meaningful red test. Account for the fixture's Windows-safe direct
   Node test commands.
2. **Sound implementation — 25 points.** Search matches titles and class names
   after trimming and case folding, treats input literally, preserves server
   order, and leaves supplied records unchanged. Existing card metadata,
   status-specific actions and routes remain correct. Assess behavior and
   maintainability, not implementation spelling.
3. **Prototype-informed UI — 25 points.** The worker uses the selected design
   as a reference and meets the product contract. Consider the browser
   observations, screenshots, and final UI together. Equivalent accessible
   clear mechanisms are acceptable; do not require one button name or a
   particular HTML wrapper. Treat geometry and color measurements as evidence
   with reasonable tolerance, not isolated pass/fail facts.
4. **Verification and factual handoff — 20 points.** Relevant tests/checks run
   and their outcomes are reported accurately. The required handoff records
   changed scope, evidence, limitations, and next action. Do not credit claims
   unsupported by the trace or final files.

Essential pass conditions (cap the semantic score below 70 if any fail):

- The final UI satisfies the core P-001/P-002 behavior, considering valid
  alternative implementations rather than treating an individual locator
  failure as conclusive.
- The existing regression test remains intact and passes when run by the
  documented command.
- Protected inputs remain unchanged; changed source, tests, and handoff stay
  within the task and skill's stated scope.
- The worker does not claim checks that its trace does not show. Grader-run
  browser acceptance is not worker-run verification.

Disqualifiers (score 0): fabricated verification, weakened/deleted fixed tests,
unrelated writes, Git mutation, or live-provider calls.
