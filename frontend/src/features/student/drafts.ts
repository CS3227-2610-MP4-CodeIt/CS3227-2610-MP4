// Code drafts in localStorage (frontend-student §1.1). A convenience, not a guarantee: any storage
// error is swallowed.

export const draftKey = (userId: number, aid: number, qid: number) => `draft:${userId}:${aid}:${qid}`;

export function loadDraft(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function saveDraft(key: string, code: string) {
  try {
    localStorage.setItem(key, code);
  } catch {
    // full or unavailable storage: skip saving
  }
}

/**
 * The editor's first content (§1.2): the draft, else the latest submission's code, else empty.
 * `null` while still loading what decides it.
 */
export function initialCode(
  draft: string | null,
  latest: { status: "pending" | "error" } | { status: "none" } | { status: "loaded"; code: string },
): string | null {
  if (draft !== null) return draft;
  if (latest.status === "pending") return null;
  return latest.status === "loaded" ? latest.code : "";
}
