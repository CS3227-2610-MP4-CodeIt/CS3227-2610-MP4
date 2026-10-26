import { beforeEach, describe, expect, it } from "vitest";
import { emptyHistory, historyKey, loadHistory, saveHistory, started, withJob } from "./draftHistory";

const store = new Map<string, string>();
globalThis.sessionStorage = {
  getItem: (k: string) => store.get(k) ?? null,
  setItem: (k: string, v: string) => void store.set(k, v),
  removeItem: (k: string) => void store.delete(k),
  clear: () => store.clear(),
  key: () => null,
  length: 0,
} as Storage;

beforeEach(() => store.clear());

describe("draft history", () => {
  it("round-trips through sessionStorage per user", () => {
    const h = { jobIds: [3, 5], selectedId: 5, prompt: "grid bfs" };
    saveHistory(7, h);
    expect(loadHistory(7)).toEqual(h);
    expect(loadHistory(8)).toEqual(emptyHistory());
  });

  it("treats a corrupt entry as empty", () => {
    store.set(historyKey(7), "{not json");
    expect(loadHistory(7)).toEqual(emptyHistory());
    store.set(historyKey(7), JSON.stringify({ jobIds: ["x"], selectedId: null, prompt: "" }));
    expect(loadHistory(7)).toEqual(emptyHistory());
  });

  it("appends an unseen id once and ignores none", () => {
    const h = withJob(emptyHistory(), 4);
    expect(h.jobIds).toEqual([4]);
    expect(withJob(h, 4)).toBe(h);
    expect(withJob(h, null)).toBe(h);
  });

  it("selects a started job and keeps its prompt", () => {
    const h = started({ jobIds: [1], selectedId: 1, prompt: "old" }, 2, "new");
    expect(h).toEqual({ jobIds: [1, 2], selectedId: 2, prompt: "new" });
  });
});
