import { useCallback, useEffect, useMemo, useState } from "react";
import { saveDraft } from "./drafts";

const DEBOUNCE_MS = 1000;

export type DraftSaveStatus = "saving" | "saved" | "unavailable";

type DraftWriter = (key: string, code: string) => boolean;

export function createDraftSaver(
  key: string,
  onStatus: (status: DraftSaveStatus) => void,
  write: DraftWriter = saveDraft,
) {
  let pending: string | null = null;
  let timer: ReturnType<typeof setTimeout> | undefined;

  const flush = () => {
    clearTimeout(timer);
    if (pending === null) return;
    const code = pending;
    pending = null;
    onStatus(write(key, code) ? "saved" : "unavailable");
  };

  const schedule = (code: string) => {
    pending = code;
    onStatus("saving");
    clearTimeout(timer);
    timer = setTimeout(flush, DEBOUNCE_MS);
  };

  return { schedule, flush };
}

/**
 * Returns a debounced scheduler and its latest local-save status. A pending save is flushed when
 * the page is left (unmount or tab close), preserving frontend-student §1.1.
 */
export function useDraftSaver(key: string) {
  const [status, setStatus] = useState<DraftSaveStatus | null>(null);
  const saver = useMemo(() => createDraftSaver(key, setStatus), [key]);

  useEffect(() => {
    window.addEventListener("pagehide", saver.flush);
    return () => {
      window.removeEventListener("pagehide", saver.flush);
      saver.flush();
    };
  }, [saver]);

  const schedule = useCallback((code: string) => saver.schedule(code), [saver]);
  return { schedule, status };
}
