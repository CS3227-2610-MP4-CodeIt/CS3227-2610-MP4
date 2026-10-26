import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Raw HTML is not rendered (no rehype-raw); the default urlTransform drops `javascript:` etc.
 * Links open in a new tab; images are shown as links, never loaded (frontend-spec §6).
 */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-sm max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ node: _node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" />,
          img: ({ src, alt }) =>
            typeof src === "string" && src ? (
              <a href={src} target="_blank" rel="noopener noreferrer">
                {alt || src}
              </a>
            ) : null,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
