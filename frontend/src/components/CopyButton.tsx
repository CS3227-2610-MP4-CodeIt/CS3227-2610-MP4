import { useState } from "react";

/** Small "Copy" button that shows "Copied" for a moment. */
export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () =>
    void navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  return (
    <button type="button" className="btn px-2 py-0.5 text-xs" onClick={copy}>
      {copied ? "Copied" : label}
    </button>
  );
}
