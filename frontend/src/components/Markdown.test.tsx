import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Markdown, normalizeMathDelimiters } from "./Markdown";

describe("Markdown", () => {
  it("does not render raw HTML or javascript: links", () => {
    const html = renderToStaticMarkup(
      <Markdown>
        {
          '<script>alert(1)</script>\n\n[click](javascript:alert(1)) <img src=x onerror="alert(1)">'
        }
      </Markdown>,
    );
    expect(html).not.toContain("<script");
    expect(html).not.toContain("javascript:");
    expect(html).not.toContain("<img");
  });

  it("renders images as links and opens links in a new tab", () => {
    const html = renderToStaticMarkup(
      <Markdown>
        {"![pic](https://e.com/a.png) [site](https://e.com)"}
      </Markdown>,
    );
    expect(html).not.toContain("<img");
    expect(html).toContain('href="https://e.com/a.png"');
    expect(html).toContain('rel="noopener noreferrer"');
  });
});

describe("normalizeMathDelimiters", () => {
  it("rewrites \\(..\\) and \\[..\\] to dollar delimiters", () => {
    expect(
      normalizeMathDelimiters(
        "length \\(L_i\\) and \\(\\lfloor L_i / x \\rfloor\\)",
      ),
    ).toBe("length $L_i$ and $\\lfloor L_i / x \\rfloor$");
    expect(normalizeMathDelimiters("\\[\n1 \\le n\n\\]")).toBe(
      "$$\n1 \\le n\n$$",
    );
  });

  it("leaves code spans and fences untouched", () => {
    const md = "`\\(x\\)`\n\n```\n\\(y\\)\n```";
    expect(normalizeMathDelimiters(md)).toBe(md);
  });

  it("leaves existing $ / $$ math untouched (e.g. \\\\[2pt] line breaks)", () => {
    const md =
      "$$\\begin{aligned} a \\\\[2pt] b \\end{aligned}$$ and $f\\(x\\)$ then \\[y\\]";
    expect(normalizeMathDelimiters(md)).toBe(
      "$$\\begin{aligned} a \\\\[2pt] b \\end{aligned}$$ and $f\\(x\\)$ then $$y$$",
    );
  });

  it("ignores delimiters preceded by a backslash", () => {
    const md = "line \\\\[2pt] and \\\\(x\\\\)";
    expect(normalizeMathDelimiters(md)).toBe(md);
  });

  it("does not match across a blank line", () => {
    const md = "lone \\( paren\n\nnext para \\) end";
    expect(normalizeMathDelimiters(md)).toBe(md);
    expect(normalizeMathDelimiters("\\(a\nb\\)")).toBe("$a\nb$");
  });

  it("renders \\(..\\) math with KaTeX", () => {
    const html = renderToStaticMarkup(
      <Markdown>{"(\\(1 \\le n \\le 10^{5}\\))"}</Markdown>,
    );
    expect(html).toContain("katex");
    expect(html).toContain("≤");
  });
});
