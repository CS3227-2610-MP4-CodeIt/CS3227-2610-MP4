import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ResultTabs, nextResultTab } from "./ResultTabs";

describe("result navigation", () => {
  it("wraps arrows, supports Home/End and leaves Tab native", () => {
    expect(nextResultTab("run", "ArrowLeft")).toBe("submissions");
    expect(nextResultTab("submissions", "ArrowRight")).toBe("run");
    expect(nextResultTab("hint", "Home")).toBe("run");
    expect(nextResultTab("hint", "End")).toBe("submissions");
    expect(nextResultTab("hint", "Tab")).toBeNull();
  });
  it("names and links stable panels with one tabbable selected tab", () => {
    const html = renderToStaticMarkup(
      <ResultTabs
        selected="hint"
        onSelect={() => {}}
        panels={{
          run: "run content",
          submit: "submit content",
          hint: "hint content",
          submissions: "history content",
        }}
      />,
    );
    expect(html).toContain('aria-label="Question results"');
    expect(html.match(/tabindex="0"/g)).toHaveLength(2);
    expect(html.match(/tabindex="-1"/g)).toHaveLength(3);
    for (const id of ["run", "submit", "hint", "submissions"]) {
      expect(html).toContain(`aria-controls="result-panel-${id}"`);
      expect(html).toContain(`aria-labelledby="result-tab-${id}"`);
    }
    expect(html).toContain(
      'id="result-panel-run" role="tabpanel" aria-labelledby="result-tab-run" hidden=""',
    );
    expect(html).toContain(
      'id="result-tab-hint" role="tab" type="button" aria-selected="true"',
    );
  });
});
