import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createDraftSaver } from "./useDraftSaver";

describe("createDraftSaver", () => {
  let saved: string[];
  let status: string[];
  let saver: ReturnType<typeof createDraftSaver>;

  beforeEach(() => {
    vi.useFakeTimers();
    saved = [];
    status = [];
    saver = createDraftSaver(
      "draft:1:2:3",
      (next) => status.push(next),
      (_key, code) => {
        saved.push(code);
        return true;
      },
    );
  });

  afterEach(() => vi.useRealTimers());

  it("shows saving, then saved after the debounce", () => {
    saver.schedule("first");
    expect(status).toEqual(["saving"]);
    vi.advanceTimersByTime(1000);
    expect(saved).toEqual(["first"]);
    expect(status).toEqual(["saving", "saved"]);
  });

  it("debounces edits and writes only the latest value", () => {
    saver.schedule("first");
    vi.advanceTimersByTime(500);
    saver.schedule("latest");
    vi.advanceTimersByTime(1000);
    expect(saved).toEqual(["latest"]);
  });

  it("reports unavailable storage when a write fails", () => {
    saver = createDraftSaver(
      "draft:1:2:3",
      (next) => status.push(next),
      () => false,
    );
    saver.schedule("code");
    vi.advanceTimersByTime(1000);
    expect(status).toEqual(["saving", "unavailable"]);
  });

  it("flushes a pending write immediately", () => {
    saver.schedule("code");
    saver.flush();
    vi.advanceTimersByTime(1000);
    expect(saved).toEqual(["code"]);
  });
});
