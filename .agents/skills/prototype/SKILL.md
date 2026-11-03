---
name: prototype
description: Prototype a frontend design during task planning when words leave a material layout or interaction decision unclear; use an approved interactive comparison to capture the chosen direction for implementation.
---

# Prototype for task alignment

Use a prototype to close the gap between a written task and the frontend the user expects. The prototype is a temporary, clickable design conversation. Its outcome is an agreed design reference and clearer task criteria; it is not the feature implementation.

## Ask before prototyping

When the agent sees a UI decision that would be easier to settle visually, ask the user whether they want a throwaway prototype to align on it. Wait for an explicit yes before creating or changing prototype files. If the user declines, continue planning through discussion and examples in words. A direct request to build a prototype is approval for that requested prototype.

## Run the design conversation

1. Identify the specific screen, user goal, and unresolved choice from the planning conversation. Keep the prototype narrow enough to answer that choice.
2. Inspect the current screen when one exists. Use it as the baseline so alternatives can be judged in the real product context.
3. Create a small set of meaningfully different UI alternatives, usually three. Provide simple previous/next controls near the bottom of the page and show which version is selected. When the prototype revises an existing design, include a bottom control to compare the proposed changes with the current version.
4. Add controls for mock data or UI states when they could change the user's decision. Add toggles for proposed ideas so the user can assess each independently. Keep these controls visibly part of the prototype, and make each one change the presented experience.
5. Keep prototype behavior local and reversible. Use labeled mock data for speculative states and local stubs for proposed interactions. Clearly mark the prototype as an exploration so it cannot be mistaken for a finished feature.
6. Show the user how to open and explore it. Ask what they want to keep; accept a chosen variant, a combination of parts, or a new direction. The user makes the design choice.
7. Return the decision to planning with the selected version or elements, expected interactions, important data/states, unresolved questions, and a stable prototype pointer. If the decision changes task scope, the revised task needs user approval before it becomes READY.

## Keep the handoff useful

Return a stable prototype revision and the selected version or combination so the task brief can link them. The implementer uses that reference to reproduce the agreed UI, including its important states and interactions. The finished UI is checked against the chosen design; comparison controls and losing alternatives stay out of production.

Keep prototype code isolated from production code, preferably in a disposable route or branch consistent with the repository workflow. Preserve a runnable pointer for the planning handoff; keep the production change focused on the chosen design.

## Completion

Complete the handoff when the user's choice, required UI behavior, and prototype pointer are returned to planning. If the user has not chosen, return the open decision; the task is not design-settled.
