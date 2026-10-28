import { useCallback, useEffect, useRef } from "react";
import { saveDraft } from "./drafts";

const DEBOUNCE_MS = 1000;

/**
 * Returns `schedule(code)`: saves the draft 1 s after the last call, and once more when the page
 * is left (unmount or tab close) if a save is still pending (frontend-student §1.1).
 */
export function useDraftSaver(key: string) {
  const pending = useRef<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const flush = useCallback(() => {
    clearTimeout(timer.current);
    if (pending.current === null) return;
    saveDraft(key, pending.current);
    pending.current = null;
  }, [key]);

  useEffect(() => {
    window.addEventListener("pagehide", flush);
    return () => {
      window.removeEventListener("pagehide", flush);
      flush();
    };
  }, [flush]);

  return useCallback(
    (code: string) => {
      pending.current = code;
      clearTimeout(timer.current);
      timer.current = setTimeout(flush, DEBOUNCE_MS);
    },
    [flush],
  );
}
