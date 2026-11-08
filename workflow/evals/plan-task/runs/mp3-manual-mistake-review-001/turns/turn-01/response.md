The current app already supports post-submission results, including:

- Score and percentage
- Each question
- The student’s selected answer
- The correct answer
- The explanation
- A “View results” entry point from the student quiz list

The planning gap is review ergonomics: students can see the information, but there is no focused way to locate missed questions quickly.

Before I write the task brief, please choose the intended review behavior:

1. **Incorrect-only plus all questions (recommended)**  
   Add a clear incorrect-only view or filter while preserving an all-questions view. This best supports quickly finding mistakes without removing access to the full review.

2. **All questions with mistakes emphasized**  
   Keep one review page, but add stronger incorrect/correct grouping, summary counts, and navigation among mistakes. This has less UI state but is less focused.

3. **Incorrect-only by default**  
   Open directly to missed questions, with a control to return to all questions. This is fastest for mistake review but makes the complete review less immediate.

Once you choose, I’ll write the self-contained planning brief under `workflow/tasks/` and mark it `READY` if no further scope decisions are needed. No implementation will be performed.