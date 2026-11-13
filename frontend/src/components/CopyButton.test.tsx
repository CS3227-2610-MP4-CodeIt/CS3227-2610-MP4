import { describe, expect, it, vi } from "vitest";
import { copyText, createCopyAttempts } from "./CopyButton";

describe("copyText", () => {
  it("copies the supplied text and reports success", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    expect(await copyText("sample", { writeText })).toBe(true);
    expect(writeText).toHaveBeenCalledWith("sample");
  });
  it("reports failure for rejected or unavailable clipboard access", async () => {
    expect(
      await copyText("sample", {
        writeText: vi.fn().mockRejectedValue(new Error("denied")),
      }),
    ).toBe(false);
    expect(await copyText("sample", undefined)).toBe(false);
  });
});

describe("copy feedback attempts", () => {
  it("clears old feedback on each attempt and ignores older completions", async () => {
    const updates: string[] = [];
    const attempt = createCopyAttempts((status) => updates.push(status));
    let resolveOld!: (value: boolean) => void;
    let resolveNew!: (value: boolean) => void;
    const old = attempt(
      () =>
        new Promise<boolean>((resolve) => {
          resolveOld = resolve;
        }),
    );
    const newer = attempt(
      () =>
        new Promise<boolean>((resolve) => {
          resolveNew = resolve;
        }),
    );
    expect(updates).toEqual(["copying", "copying"]);
    resolveNew(false);
    await newer;
    resolveOld(true);
    await old;
    expect(updates).toEqual(["copying", "copying", "failed"]);
    await attempt(async () => true);
    expect(updates.slice(-2)).toEqual(["copying", "copied"]);
    await attempt(async () => true);
    expect(updates.slice(-2)).toEqual(["copying", "copied"]);
  });
});
