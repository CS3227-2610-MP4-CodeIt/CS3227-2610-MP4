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
- How does the organization of the context affect the agent’s ability to find and follow important instructions?
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

The LLM used for supporting the AI features should be SoC LLM. You should pay attention to the restrictions (e.g., number of API calls allowed per minute), manage the use of such resources properly, and implement guardrails / error handling accordingly. For more information, please refer to: https://dochub.comp.nus.edu.sg/cf/guides/soclaas/start.

You are allowed to use SDD toolkits. However, you should be managing your specialized agents and multi-agent workflow as well to complement or to compare with the ones in the SDD toolkits (if any).

In addition, you are NOT allowed to use any build-and-host environment (e.g., the ones available in Codex / Claude). Instead, the deployment should be managed separately by your team with suitable automations (e.g., via Github Actions).

You will be asked to redo the project if you violate such restrictions.

If you are unsure, please use the forum to clarify.

# Submission Instructions

For us to grade this assignment in a timely manner, we need you to adhere strictly to the following submission guidelines. They will help us grade the assignment in an appropriate manner. You will be penalized if you do not follow these instructions.

The repo should be named as CS3227-2610-MP4 in a github organization for you team and set to be public.

It should contain:

- Any source code (src/…). This folder should contain all the codes used in your project. The code will be reviewed for code quality. (Please format it nicely. We would really appreciate it.)
- Any files related to the Agentic SE workflow (workflow/…): All the files related to the development workflow (e.g., the .md files, the scripts for the graders) should be consolidated into this folder as much as possible unless it is reasonable / natural for them to be elsewhere. (Please organize the folder properly, and provide a brief description of all these files in the developer guide.)
- A user guide (docs/UserGuide.md). This should describe all current features of your system, and how the users can access and test your system. Ensure those descriptions match the product precisely, as it will be used by peer testers (inaccuracies will be considered bugs).
- A developer guide (docs/DeveloperGuide.md). This should describe the design of your system and the relevant software engineering process, with the focus on the additional requirements listed above. It should match the latest release of the product and include an acknowledgement section citing all ideas / code / documentation you have reused.
- A product website. This should be set up using Github pages as you have done in CS2103/T.
- A reflection document (docs/Reflections.md). This should contain your reflections on Multi-Agent SE, Context Engineering and Resource-aware Use. Give concrete examples backed by experiments and result analysis.
- A folder of summary logs (logs/…). This folder should contain summaries of all the prompts and interactions that took place during the development of this app. Ask AI to produce the summaries for you, but don’t forget to verify the correctness of the generated summaries. (These summaries will come in handy when you reflect on your project.)

Make sure that your repo is named and structured as explained in this write up, and master branch is up to date. We will pull the latest version of your master branch before the deadline, which is 13 Nov (Fri), 2pm SGT, and use it for grading.

One member in your team should also submit your Github organization name through the relevant Canvas quiz by 23 Oct (Fri), 2pm SGT. (Note: The submission is still required even if the team formation is the same.)

There absolutely will be no extensions to the deadline of this assignment. Read the Grading page in Canvas if you are unsure about the late submission penalty.

In addition, we will also access your repo on Github during the grading process so please make sure that the repo is accessible and there are no further changes to it after your submission.