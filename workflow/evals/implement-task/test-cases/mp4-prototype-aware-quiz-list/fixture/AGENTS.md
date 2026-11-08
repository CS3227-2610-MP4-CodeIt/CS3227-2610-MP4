# Fixture instructions

Use `workflow/tasks/quiz-list.md` and `specs/product.md` as the task and behavior
contract. The approved layout and interaction reference is linked from the task
brief at `frontend/prototype/selected.html`. Product behavior in the spec takes
precedence if a visual detail appears to conflict with it.

Keep source changes within `frontend/src/` and add focused tests under
`frontend/tests/`. Write the required factual handoff as a unique
`workflow/implementations/<task-id>-<run-id>.md` file. Preserve the approved
prototype, product contract, data, existing regression test, and task brief. Do
not install dependencies, use live services, mutate Git state, or perform an
independent review. Run the available Node checks.
