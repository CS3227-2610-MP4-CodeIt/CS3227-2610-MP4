import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("primary readiness", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubEnv("VITE_API_BASE_URL", "https://pi.example.com");
    vi.stubEnv("VITE_API_FALLBACK_URL", "https://backup.example.com");
    vi.stubGlobal("window", globalThis);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("keeps a healthy primary that responds after 3.5 seconds", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init: RequestInit) =>
          new Promise((resolve, reject) => {
            const timer = setTimeout(
              () => resolve(new Response(null, { status: 200 })),
              3500,
            );
            init.signal?.addEventListener("abort", () => {
              clearTimeout(timer);
              reject(new DOMException("Request cancelled", "AbortError"));
            });
          }),
      ),
    );
    const { resolveApiBase } = await import("./origin");
    const result = resolveApiBase();
    await vi.advanceTimersByTimeAsync(3500);
    await expect(result).resolves.toBe("https://pi.example.com/api");
  });

  it("retries once before selecting the backup", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("Temporary network failure"))
      .mockResolvedValueOnce(new Response(null, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const { resolveApiBase } = await import("./origin");
    await expect(resolveApiBase()).resolves.toBe("https://pi.example.com/api");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("selects the backup after both readiness checks fail", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValue(new TypeError("Network failure"));
    vi.stubGlobal("fetch", fetchMock);
    const { resolveApiBase } = await import("./origin");
    await expect(resolveApiBase()).resolves.toBe(
      "https://backup.example.com/api",
    );
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("selects the backup when both attempts time out", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn(
      (_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) => {
          init.signal?.addEventListener("abort", () => {
            reject(new DOMException("Request cancelled", "AbortError"));
          });
        }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { resolveApiBase } = await import("./origin");
    const result = resolveApiBase();
    await vi.advanceTimersByTimeAsync(16_000);
    await expect(result).resolves.toBe("https://backup.example.com/api");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
