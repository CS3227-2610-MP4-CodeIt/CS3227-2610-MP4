import { beforeEach, describe, expect, it } from "vitest";
import { draftKey, initialCode, loadDraft, saveDraft } from "./drafts";

const store = new Map<string, string>();
let full = false;
globalThis.localStorage = {
  getItem: (k: string) => store.get(k) ?? null,
  setItem: (k: string, v: string) => {
    if (full) throw new DOMException("full", "QuotaExceededError");
    store.set(k, v);
  },
  removeItem: (k: string) => void store.delete(k),
  clear: () => store.clear(),
  key: () => null,
  length: 0,
} as Storage;

beforeEach(() => {
  store.clear();
  full = false;
});

describe("drafts", () => {
  it("keys drafts per user, assignment and question", () => {
    saveDraft(draftKey(1, 2, 3), "print(1)");
    expect(loadDraft(draftKey(1, 2, 3))).toBe("print(1)");
    expect(loadDraft(draftKey(9, 2, 3))).toBeNull();
    expect(loadDraft(draftKey(1, 2, 4))).toBeNull();
  });

  it("skips saving when storage is full", () => {
    full = true;
    expect(() => saveDraft(draftKey(1, 2, 3), "x")).not.toThrow();
    expect(loadDraft(draftKey(1, 2, 3))).toBeNull();
  });

  it("keeps an empty draft as a draft", () => {
    saveDraft(draftKey(1, 2, 3), "");
    expect(initialCode(loadDraft(draftKey(1, 2, 3)), { status: "loaded", code: "old" })).toBe("");
  });
});

describe("initialCode", () => {
  it("prefers the draft without waiting for submissions", () => {
    expect(initialCode("draft", { status: "pending" })).toBe("draft");
  });

  it("falls back to the latest submission, then empty", () => {
    expect(initialCode(null, { status: "pending" })).toBeNull();
    expect(initialCode(null, { status: "loaded", code: "sub" })).toBe("sub");
    expect(initialCode(null, { status: "none" })).toBe("");
    expect(initialCode(null, { status: "error" })).toBe("");
  });
});
