import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Markdown } from "./Markdown";

describe("Markdown", () => {
  it("does not render raw HTML or javascript: links", () => {
    const html = renderToStaticMarkup(
      <Markdown>{'<script>alert(1)</script>\n\n[click](javascript:alert(1)) <img src=x onerror="alert(1)">'}</Markdown>,
    );
    expect(html).not.toContain("<script");
    expect(html).not.toContain("javascript:");
    expect(html).not.toContain("<img");
  });

  it("renders images as links and opens links in a new tab", () => {
    const html = renderToStaticMarkup(<Markdown>{"![pic](https://e.com/a.png) [site](https://e.com)"}</Markdown>);
    expect(html).not.toContain("<img");
    expect(html).toContain('href="https://e.com/a.png"');
    expect(html).toContain('rel="noopener noreferrer"');
  });
});
