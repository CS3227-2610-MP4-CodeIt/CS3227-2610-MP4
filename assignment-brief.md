# Project Description

In this project, you will develop a production-level, AI-infused, secured web app using Multi-Agentic SE features as part of the software development process.

The app should still have multiple user roles and it must be related to programming / software engineering (e.g., for learning python programming / automating code reviews) with the following requirements:

- There should be at least one LLM-based AI feature for each role.
- Spec-Driven Development and Multi-Agent SE (i.e., specialized agents with proper coordination) should be followed in the development process.
- Explicit implementation and testing of security features for the AI features developed and in the development process are required.
- The app should be deployed online and there should be proper separation between the development and the production environment.
- There should be evidence of Context Engineering and Resource-aware Use in the app and in the development process.

The user interface should be kept simple. All shared components (e.g., data storage) should be properly designed (e.g., with SRP and DRY).

It is up to you to define the exact features for each user role.

However, in general, if there are N (= 2 or 3) students in your team, there should be N different user roles with the relevant features.

Each of the student should complete all the features in a set and a good portion of the work at the team-level. The estimate individual workload should be 1.5 times the level of MP1.

In addition, as you work on the project, you should reflect on Muti-Agent SE, as well as Context Engineering and Resource-aware Use, and create a reflection document on these topics.

Here are some sample questions that you can use to guide your reflections.

## Muti-Agent SE

- How to design and implement the coordination pattern for multiple agents?
- How to verify that the coordination patterns are properly followed in terms of triggering, context management, resource sharing and hands-off)?
- Were any agents idle, overloaded, or blocked while waiting for others?
- Did retries, repeated analysis, or unnecessary tool calls consume resources?
- How to resolve conflicts / disagreements between agents (if any)?
- Did the benefits of multi-agent coordination outweigh the costs?
- When should multi-agent coordination be used and when not?

## Context Engineering and Resource-aware Use

- How to engineer the system prompt and the skills for the agents?
- When should information be supplied upfront, and when should the agent retrieve it as needed?
- How does the organization of the context affect the agent's ability to find and follow important instructions?
- What should be recorded in notes.md or a handoff document so another agent can continue efficiently?
- When has adding more context made an agent less effective? What signals revealed the problem?
- How to choose / configurate the model based on the tasks and the resource constraints?
- What should be done to reduce the cache miss? How much did it help to reduce the actual token usage?
- What is the percentage of tokens used in the internal reasoning for a specific task? How could persisted reasoning help?
- What other approaches have you experimented to monitor and reduce token usage?
- Which types of tasks consume the most tokens in your workflow? Did you manage to reduce the usage for such tasks?

# Restrictions

This is a team project (i.e., no individual submissions allowed). The team size is 2~3 students.

You are NOT allowed to reuse your previous MPs.

You are allowed to use Codex / Claude for this MP.

The LLM used for supporting the AI features