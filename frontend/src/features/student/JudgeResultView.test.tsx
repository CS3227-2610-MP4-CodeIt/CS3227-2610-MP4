import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { formatDate } from "../../components/dates";
import { JudgeResultView } from "./JudgeResultView";

describe("submission results", () => {
  it("shows sent time without exposing hidden test output", () => {
    const sentAt = "2026-01-02T12:00:00Z";
    const html = renderToStaticMarkup(
      <JudgeResultView
        sentAt={sentAt}
        visibleTests={[]}
        result={{
          verdict: "WRONG_ANSWER",
          passed: 0,
          total: 1,
          failed_test_index: 0,
          error_message: null,
          max_time_ms: 1,
          max_memory_kb: 1024,
          results: [
            {
              index: 0,
              hidden: true,
              status: "WRONG_ANSWER",
              time_ms: 1,
              memory_kb: 1024,
              stdout_preview: "private-output",
              stderr_preview: "private-error",
            },
          ],
        }}
      />,
    );
    expect(html).toContain(`Result for the code sent at ${formatDate(sentAt)}`);
    expect(html).toContain("Hidden test");
    expect(html).not.toContain("private-output");
    expect(html).not.toContain("private-error");
  });
});
