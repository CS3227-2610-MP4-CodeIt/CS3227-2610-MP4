// The question-generation drafts seen in this tab session (frontend-teacher §2.2). The check endpoint
// only returns the latest job, so the page remembers earlier draft ids itself.

export interface DraftHistory {
  jobIds: number[];
  selectedId: number | null;
  prompt: string;
}

export const emptyHistory = (): DraftHistory => ({ jobIds: [], selectedId: null, prompt: "" });

export const historyKey = (userId: number) => `qgen:${userId}`;

export function loadHistory(userId: number): DraftHistory {
  try {
    const value = JSON.parse(sessionStorage.getItem(historyKey(userId)) ?? "null");
    if (
      Array.isArray(value?.jobIds) &&
      value.jobIds.every((id: unknown) => typeof id === "number") &&
      (value.selectedId === null || typeof value.selectedId === "number") &&
      typeof value.prompt === "string"
    ) {
      return { jobIds: value.jobIds, selectedId: value.selectedId, prompt: value.prompt };
    }
  } catch {
    // unavailable storage or a corrupt entry: start empty
  }
  return emptyHistory();
}

export function saveHistory(userId: number, history: DraftHistory) {
  try {
    sessionStorage.setItem(historyKey(userId), JSON.stringify(history));
  } catch {
    // unavailable storage: the history lasts until the page is left
  }
}

/** Append a job id not seen yet (e.g. the latest job, maybe started in another tab). */
export function withJob(history: DraftHistory, id: number | null | undefined): DraftHistory {
  if (id == null || history.jobIds.includes(id)) return history;
  return { ...history, jobIds: [...history.jobIds, id] };
}

/** A generation was started: remember it, select it and keep its prompt for later revisions. */
export const started = (history: DraftHistory, id: number, prompt: string): DraftHistory => ({
  ...withJob(history, id),
  selectedId: id,
  prompt,
});
