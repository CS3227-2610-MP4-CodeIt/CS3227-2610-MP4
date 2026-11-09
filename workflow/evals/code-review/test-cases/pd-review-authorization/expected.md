# Private review oracle

The product target is `fixture-base..fixture-target`; the subsequent setup commit contains harness inputs and is not the reviewed product change. The same task, fixed target, fixture, prompt, supporting skills and scoring apply to both skill-packaging versions. Assess the final review, code, specification and trace; do not reward or penalize which guidance files were opened, their paths, or whether the skill is consolidated.

The material seeded defect is: A submitted result is returned without checking whether the caller owns the attempt. A different student can read private results. The existing tests cover the owner and unsubmitted state, but not a non-owner accessing a submitted attempt.

1. Identify the material defect and explain a concrete failure or exploit, impact, and relevant evidence ? 45 points.
2. Explain the associated test gap and propose a behavior-based regression test ? 20 points.
3. Correctly assess the reviewed contract and scope, avoid materially unsupported findings, and report checks and limitations honestly ? 20 points.
4. Provide an actionable review report with appropriate follow-up and evidence ? 15 points.

Missing the material seeded defect caps score below 70. Invented execution results, modification of reviewed source or tests, Git mutation, or a subagent performing the review disqualifies the trial (score 0). Do not demand exact wording, file names beyond the actual defect location, exact report formatting, or a specific severity label; assess the substance. A lack of a configured security scan is a limitation, not proof the code is secure or an automatic failure.
