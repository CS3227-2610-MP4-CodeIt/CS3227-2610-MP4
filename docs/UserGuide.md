# CodeIt User Guide

CodeIt helps teachers create Python programming assignments, students solve them with automated judging and AI hints, and administrators manage classes and review progress. This guide describes the implemented interface as reviewed on 28 October 2026.

## 1. Access and accounts

For a local installation, open **http://localhost:5173** after following the [Developer Guide setup](DeveloperGuide.md#3-local-setup). A public deployment URL and hosted peer-test credentials are not recorded in the repository; use the address and accounts supplied by the team for a hosted installation.

Sign in with your username and password. Your role determines which navigation links you see. There is no public account registration: an administrator creates teacher and student accounts. Admin accounts are provisioned during server setup.

In development mode, the server seeds these accounts and classes:

| Account | Password | Membership |
| --- | --- | --- |
| `teacher1` | `demo1234` | Demo Class A |
| `teacher2` | `demo1234` | Demo Class B |
| `student01`–`student10` | `demo1234` | Demo Class A |
| `student11`–`student20` | `demo1234` | Demo Class B |
| `admin` | See note below | Administrator |

**Admin password:** if a bootstrap admin is configured, use its configured password. The supplied backend environment example sets it to `change-me`. Only when bootstrap has not already created an admin does development seeding create `admin` with `demo1234`. Existing accounts keep their passwords across restarts; production does not seed demo accounts. Ask the installation owner if neither documented initial password applies.

The seed creates accounts and classes, but no questions or assignments. An empty assignment list on a new installation is expected. Section 7 provides a complete setup and testing walkthrough.

Use **Log out** in the header when finished. Login state is shared between tabs in the same browser profile, so use separate browser profiles/private sessions to test roles simultaneously. Sessions expire after 12 hours by default. Password resets by an admin end that user's existing sessions.

## 2. Students: solve an assignment

### Find a question

1. Sign in as a student and open **Assignments**.
2. Open an assignment from one of your classes.
3. Read its description, due date and ordered questions, then open a question.

The question workspace shows the statement, difficulty, execution limits and sample tests beside a Python editor. You can resize the statement/editor split and the editor height. Sample inputs and expected outputs have copy controls. Dates are displayed in your browser's local time zone.

Write a complete Python program that reads standard input and prints only the required output. Do not include interactive prompts such as `Enter a number:` unless the question explicitly requires them. The judge does not install packages for individual submissions.

### Run and submit

| Action | What it does |
| --- | --- |
| **Run** | Checks the current code against visible sample tests. Does not create a submission record or mark the question solved. |
| **Submit** | Checks visible tests first, then hidden tests, and saves the judged submission. An accepted submission marks the question solved. |
| **Get hint** | Requests AI guidance for the current question and code. You can first fill in “What are you stuck on?” with up to 500 characters. |

Run and Submit require nonblank code. Hints can be requested with an empty editor. Submitted code is limited to 64 KiB. You can keep editing while work is running, but results correspond to the code sent when you clicked the action. If a matching action is already running, CodeIt shows it and does not send your new code; wait, then click again to check the revised version.

Results appear in **Run result**, **Submit result**, **Hint** and **Submissions** tabs. The judge stops at the first failing test, so a failed result need not include every test. Hidden test inputs, expected outputs and output/error previews are withheld. Visible test results can show output and error details.

| Verdict | Meaning and next step |
| --- | --- |
| Accepted | All tests included in that action passed. Submit successfully to record a solution. |
| Wrong answer | Printed output differs from the expected output; check formatting and edge cases. |
| Time limit exceeded | The program ran too long; check loops and algorithm complexity. |
| Memory limit exceeded | The program exceeded its memory allowance; inspect large allocations. |
| Runtime error | The program failed during execution, including syntax errors; inspect visible error details when available. |

Comparison normally preserves leading/internal spaces while ignoring trailing spaces on each line and trailing blank lines. A teacher can enable numerical tolerance for floating-point answers. Check the question's displayed limits and tolerance rather than assuming every problem uses the same settings.

### Use AI hints

Enter an optional specific question, such as “Why does this fail when the input is zero?”, and choose **Get hint**. The AI may retrieve the question's visible tests and your code. A “Looked at” note identifies which of those sources it used. It cannot retrieve hidden tests through the hint tools.

Hints may be incomplete or incorrect. Check the suggestion against the statement and visible tests. Requests containing text that resembles instructions to override the AI's rules can be rejected; remove that text from your question or code comments and try again. A rejected hint request does not prevent using Run or Submit.

### Save and revisit code

Code edits are saved as a browser-local draft when browser storage is available. On reopening a question, CodeIt uses the draft first, otherwise your latest submitted code, otherwise an empty editor. Drafts are tied to your account, assignment, question and browser; they do not synchronize across devices and can be lost if browser storage is cleared or unavailable. Keep a separate copy of important work.

Open **Submissions**, select a row and inspect its saved code, time, verdict and passed count. **Load into editor** asks for confirmation before replacing the current draft. Loading code does not run it or create a new submission.

At the due date, **Submit** becomes **Submissions closed**. The server also checks deadlines. Run, hints and viewing previous submissions remain available while you still have access to the assignment. Ask your teacher about a deadline extension if required.

## 3. Teachers: questions and assignments

### Maintain your question bank

Open **Questions** to see your own questions, including an **AI** badge for approved generated questions. Choose **New question** and enter:

| Field | Rules |
| --- | --- |
| Title | 1–200 characters |
| Statement | Markdown, 1–20,000 characters; use the preview to check formatting |
| Difficulty | `easy`, `medium` or `hard` |
| Topics | Optional; at most five comma-separated topics, each 1–30 characters; normalized to lowercase and deduplicated |
| Time limit | 100–10,000 milliseconds |
| Memory limit | 16–1,024 MB |
| Float tolerance | Optional absolute/relative tolerances between 0 and 1; at least one must be positive |
| Test cases | 2–50 cases, with at least one visible and one hidden; each input and expected output is at most 1 MiB |

Use **Add test case**, the arrow controls and **Remove** to manage test order. Mark **Hidden** for tests students should not see. Choose **Create question**, or **Save** when editing an existing question. A question cannot be deleted while an assignment uses it.

Questions are shared by reference across your assignments. Editing a question updates the assigned question too, without automatically rejudging older submissions. Review changes carefully once students have started.

### Generate and revise with AI

1. Open **Generate**, or choose **Generate with AI** from Questions.
2. Select difficulty, enter one to five topics and a prompt of up to 2,000 characters. For example: “Create an introductory problem that reads one integer and prints its square. Include a zero case.”
3. Choose **Generate** and wait for the draft.
4. Review its statement, limits, visible/hidden tests and reference solution. Expected outputs are written by the AI and may be wrong; independently check them against the solution before approval.
5. To change the draft, enter feedback under **Revise this draft** and choose **Revise**. Each revision creates another draft.
6. Choose **Approve** to create an editable question in your question bank. Approval does not publish an assignment. Edit the approved question if needed, then add it to an assignment.

**Drafts this session** lets you select earlier generated drafts. Its navigation history is stored for the current browser tab session; closing the session can lose that list. Approval is allowed once per draft. Only one generation/revision can run per teacher at a time.

### Create and manage assignments

1. Open **Assignments** and choose **New assignment**.
2. Select one of your classes. If none are available, ask an admin to add you to a class.
3. Enter a title, optional Markdown description and optional due date in your local time.
4. Add one to three questions from your question bank and order them with the arrows.
5. Choose **Create assignment**. It becomes available to students in that class immediately; there is no separate publish action.

The assignment list can be filtered by class. Open an assignment to view its questions/description, edit its fields or clear its due date. Only the creating teacher can edit or delete it. Other teachers in the class can read it and open its questions in a read-only view, including test cases. Their personal question bank still contains only their own questions.

A question with submissions cannot be removed from an assignment. Deleting an assignment also deletes its submissions and asks for confirmation.

## 4. Administrators: accounts, classes and summaries

### Manage accounts

Open **Users** to list accounts or filter by role. In **New user**, supply a username, display name, password and either `teacher` or `student`, then choose **Create user**.

Usernames must be 3–32 characters using letters, digits, `_`, `.` or `-`, and are unique without regard to case. Display names are 1–100 characters. Passwords must be 8–128 characters. Admin creation and role changes are not available in this form.

Open a user to change their username/display name or reset their password. Leave the password blank to retain it. A password change ends all of that user's sessions, including your own if you edit yourself. The detail page also links to the user's classes. **Delete** removes the account after confirmation; you cannot delete yourself or the last administrator.

### Manage classes

Open **Classes**, create a class with a unique name and optional description, then open its detail page. You can edit the name/description, inspect teacher and student rosters and open assignments.

Under **Add members**, search by username or name, select teachers/students and choose **Add selected**. Existing members are excluded. Use **Remove** next to a member to remove their class access. Administrators cannot be class members.

Deleting a class asks for confirmation and removes its memberships, assignments and those assignments' submissions. It does not delete the user accounts.

### Generate an assignment summary

1. Open **Classes**, select a class, then select an assignment.
2. Choose **Generate summary**.
3. Review the **Stats** table and the **AI summary — check against the numbers** panel.
4. Choose **Regenerate summary** after new submissions or roster changes when you need an updated snapshot.

The table reports current students in the class, students who attempted any question, students who solved all questions, and per-question attempted/correct student counts, total submissions and verdict counts. “Correct” means a student has at least one accepted submission; verdict totals count submissions, so repeated attempts can exceed student counts. Runs are not submissions and do not contribute.

The AI receives aggregate statistics rather than student names or source code. Its narrative is advisory; use the displayed numbers to verify it. A completed summary remains a snapshot until regenerated.

## 5. Long-running actions and connection recovery

AI requests may take several minutes; the default server deadline is five minutes. Running actions show status indicators and complete through live updates. You can leave a page and return to inspect the latest job while it is retained by the server.

If live updates disconnect, **Reconnecting live updates…** appears after a short delay. Check your connection and allow reconnection. Refresh the page if needed to retrieve the latest server state. A server restart fails unfinished jobs rather than resuming them; submit the action again after service recovery.

## 6. Troubleshooting

| Symptom | Action |
| --- | --- |
| Login fails | Check username/password and the bootstrap-admin note. Ask an admin for a reset. |
| Logged out unexpectedly | Sign in again; your session may have expired, been reset, or changed in another tab. |
| Empty class/assignment list | Ask an admin to check membership, and a teacher to create an assignment. |
| Not found / access denied | The item may be deleted or outside your role/class; return to your list and check access. |
| Form cannot be saved | Check required fields, character/number limits and visible/hidden test requirements. |
| AI unavailable, invalid response or timeout | Wait and retry after the action finishes/fails; contact the team if it persists. Avoid repeated simultaneous requests. |
| Request rejected as unsafe | Remove instructions that try to override AI rules from prompts, feedback, questions or code comments. |
| Judge busy / unavailable | Wait and retry; contact the team if the executor remains unavailable. |
| Latest edit absent from result | The action uses the code captured when clicked; wait and run/submit again. |
| Draft did not appear on another device | Drafts are browser-local. Restore from your own copy or a saved submission. |

## 7. Reproducible peer-testing walkthrough

Use a disposable development installation with the seeded accounts. This walkthrough creates real assignment/submission data; use uniquely named records on a shared test installation.

1. **Teacher setup:** sign in as `teacher1`. Under Questions, create `Peer test: integer square`, difficulty `easy`, topic `arithmetic`, time limit `2000`, memory `256`. Set the statement to “Read one integer n from standard input and print n squared.” Keep float tolerance off. Add a visible test with input `3` and expected output `9`, and a hidden test with input `0` and expected output `0`. Enter the digits in the input/output fields without surrounding quotes. Save.
2. **Assign:** create `Peer test: squares` for Demo Class A with that one question and no due date. Students in the class should see it immediately.
3. **Visible-test check:** sign out and sign in as `student01`. Open the assignment/question and Run `print(9)`. The visible test should pass. Submit the same code: it should receive Wrong answer on the hidden test, with no hidden input/output preview. Run has not created a submission; Submit has.
4. **Correct submission:** replace the editor content with the following program, then Run and Submit. Both should be Accepted, and the question should be marked solved.

   ```python
   n = int(input())
   print(n * n)
   ```

5. **History and draft:** open Submissions to see both attempts. Select the first attempt and use Load into editor, accepting the replacement confirmation. Refresh and check that the draft is retained when browser storage is available. Restore the correct code afterward.
6. **Student AI:** enter “How should I handle zero?” and choose Get hint. Expect a hint or a clear AI service error. A service error tests failure handling but does not establish a successful AI integration; retry after service recovery to complete that check.
7. **Admin AI:** sign in as the configured admin. Open Classes → Demo Class A → Peer test: squares and generate a summary. On an otherwise untouched class, expect 10 students, 1 attempted, 1 solved all, 2 submissions, 1 WA and 1 AC. Check the narrative against those numbers.
8. **Teacher AI:** sign in as `teacher1`, generate an easy arithmetic question, inspect the reference solution/tests, revise it with “Include a negative input example,” then approve the revised draft. Verify that it appears in Questions with an AI badge. AI content varies; verify validity rather than expecting exact wording.
9. **Access boundaries:** sign in as `student11` and confirm the Demo Class A assignment is absent. As admin, temporarily add `teacher2` to Demo Class A; as `teacher2`, confirm the assignment and its question are readable but assignment editing/deletion is unavailable. Remove that temporary membership afterward.
10. **Deadline:** as `teacher1`, set the test assignment's due date in the past. As `student01`, confirm Submit is closed while Run, hints and history remain available. Clear the deadline afterward if continuing tests.

A full manual pass includes successful responses from all three AI features, not only the non-AI steps. Clean up disposable test assignments/classes only when their data is no longer needed; deletion removes associated submissions.
