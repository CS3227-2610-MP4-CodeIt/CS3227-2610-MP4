import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

/**
 * LLM-written statements often use LaTeX `\(...\)` / `\[...\]` delimiters, which
 * remark-math does not recognise (Markdown treats `\(` as an escaped paren and drops
 * the backslash). Rewrite them to `$...$` / `$$...$$`, leaving code and existing
 * `$`-math alone. A delimiter preceded by another backslash (e.g. the `\\[2pt]` line
 * break) is ignored, and a match never spans a blank line (paragraph break).
 */
export function normalizeMathDelimiters(md: string): string {
  // Split out code fences, `$$` math, code spans and `$` math so their contents are untouched.
  const parts = md.split(
    /(```[\s\S]*?```|~~~[\s\S]*?~~~|(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$|`[^`\n]*`|(?<!\\)\$[^$\n]+?(?<!\\)\$)/,
  );
  return parts
    .map((part, i) =>
      i % 2 === 1
        ? part
        : part
            .replace(
              /(?<!\\)\\\[((?:(?!\n[ \t]*\n)[\s\S])+?)\\\]/g,
              (_m, tex: string) => `$$${tex}$$`,
            )
            .replace(
              /(?<!\\)\\\(((?:(?!\n[ \t]*\n)[\s\S])+?)\\\)/g,
              (_m, tex: string) => `$${tex.trim()}$`,
            ),
    )
    .join("");
}

/**
 * Raw HTML is not rendered (no rehype-raw); the default urlTransform drops `javascript:` etc.
 * Math: `$...$` / `\\(...\\)` inline and `$$...$$` / `\\[...\\]` display, rendered with KaTeX.
 * Links open in a new tab; images are shown as links, never loaded (frontend-spec §6).
 */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-sm max-w-none prose-code:before:content-none prose-code:after:content-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          a: ({ node: _node, ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer" />
          ),
          img: ({ src, alt }) =>
            typeof src === "string" && src ? (
              <a href={src} target="_blank" rel="noopener noreferrer">
                {alt || src}
              </a>
            ) : null,
        }}
      >
        {normalizeMathDelimiters(children)}
      </ReactMarkdown>
    </div>
  );
}
