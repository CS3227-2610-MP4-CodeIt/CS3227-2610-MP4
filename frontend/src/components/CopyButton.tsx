import { useRef, useState } from "react";
import { flushSync } from "react-dom";

export async function copyText(
  text: string,
  clipboard: Pick<Clipboard, "writeText"> | undefined,
): Promise<boolean> {
  if (!clipboard) return false;
  try {
    await clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

type CopyStatus = "idle" | "copying" | "copied" | "failed";

export function createCopyAttempts(setStatus: (status: CopyStatus) => void) {
  let latest = 0;
  return async (copy: () => Promise<boolean>) => {
    const attempt = ++latest;
    setStatus("copying");
    const ok = await copy();
    if (attempt === latest) setStatus(ok ? "copied" : "failed");
  };
}

export function CopyButton({
  text,
  label = "Copy",
}: {
  text: string;
  label?: string;
}) {
  const [status, setStatus] = useState<CopyStatus>("idle");
  const attempts = useRef<ReturnType<typeof createCopyAttempts> | null>(null);
  attempts.current ??= createCopyAttempts((next) => {
    if (next === "copying") flushSync(() => setStatus(next));
    else setStatus(next);
  });
  return (
    <span className="inline-flex flex-wrap items-center gap-2">
      <button
        type="button"
        className="btn px-2 py-1 text-xs"
        onClick={() =>
          void attempts.current!(() => copyText(text, navigator.clipboard))
        }
      >
        {status === "copied" ? "Copied" : label}
      </button>
      <span role="status" className="text-xs text-slate-700">
        {status === "copying"
          ? "Copying…"
          : status === "failed"
            ? "Copy failed. Select the text and copy it manually."
            : status === "copied"
              ? "Copied to clipboard."
              : ""}
      </span>
    </span>
  );
}
