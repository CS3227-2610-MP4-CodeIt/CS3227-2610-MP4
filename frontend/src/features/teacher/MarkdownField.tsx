import { useState } from "react";
import { Markdown } from "../../components/Markdown";

/** Markdown textarea with a Write / Preview tab. */
export function MarkdownField({
  id,
  value,
  onChange,
  rows = 10,
}: {
  id: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
}) {
  const [preview, setPreview] = useState(false);
  const tab = (active: boolean) =>
    `rounded px-2 py-0.5 text-xs ${active ? "bg-slate-200 font-medium" : "text-slate-600 hover:bg-slate-100"}`;
  return (
    <div className="space-y-1">
      <div className="flex gap-1">
        <button type="button" className={tab(!preview)} onClick={() => setPreview(false)}>Write</button>
        <button type="button" className={tab(preview)} onClick={() => setPreview(true)}>Preview</button>
      </div>
      {preview ? (
        <div className="min-h-24 rounded border border-slate-200 p-2">
          {value.trim() ? <Markdown>{value}</Markdown> : <p className="text-sm text-slate-400">Nothing to preview.</p>}
        </div>
      ) : (
        <textarea
          id={id}
          className="input font-mono"
          rows={rows}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </div>
  );
}
