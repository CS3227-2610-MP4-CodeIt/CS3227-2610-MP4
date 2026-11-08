import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("API failover", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubEnv("VITE_API_BASE_URL", "https://pi.example.com");
    vi.stubEnv("VITE_API_FALLBACK_URL", "https://backup.example.com");
    vi.stubGlobal("window", globalThis);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("keeps the Pi selected when a request is cancelled", async () => {
    const aborted = new DOMException("Request cancelled", "AbortError");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 200 }))
      .mockRejectedValue(aborted);
    vi.stubGlobal("fetch", fetchMock);
    const { apiFetch } = await import("./client");
    const { getApiOrigin } = await import("./origin");
    const controller = new AbortController();
    controller.abort();

    await expect(apiFetch("/test", { signal: controller.signal })).rejects.toBe(
      aborted,
    );
    expect(getApiOrigin()).toBe("primary");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("keeps the Pi selected when an in-flight request is cancelled", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 200 }))
      .mockImplementationOnce(
        (_url: string, options: RequestInit) =>
          new Promise((_resolve, reject) => {
            options.signal?.addEventListener("abort", () => {
              reject(new DOMException("Request cancelled", "AbortError"));
            });
          }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const { apiFetch } = await import("./client");
    const { getApiOrigin } = await import("./origin");
    const controller = new AbortController();
    const request = apiFetch("/test", { signal: controller.signal });
    const rejection = expect(request).rejects.toMatchObject({
      name: "AbortError",
    });

    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    controller.abort();
    await rejection;
    expect(getApiOrigin()).toBe("primary");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("switches and retries a safe read after a genuine network failure", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 200 }))
      .mockRejectedValueOnce(new TypeError("Network failed"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ ok: true })));
    vi.stubGlobal("fetch", fetchMock);
    const { apiFetch } = await import("./client");
    const { getApiOrigin } = await import("./origin");

    await expect(apiFetch("/test")).resolves.toEqual({ ok: true });
    expect(getApiOrigin()).toBe("fallback");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "https://backup.example.com/api/test",
      expect.any(Object),
    );
  });
});
