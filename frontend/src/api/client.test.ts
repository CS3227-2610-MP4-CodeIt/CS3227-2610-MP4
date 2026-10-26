import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { saveAuth } from "../auth/session";
import { ApiError, apiFetch, setUnauthorizedHandler } from "./client";

const respond = (status: number, body?: unknown) =>
  vi.fn(async () => new Response(body === undefined ? null : JSON.stringify(body), { status }));

const user = { id: 1, username: "admin", display_name: "Admin", role: "admin" as const };

describe("apiFetch", () => {
  const onUnauthorized = vi.fn();

  beforeEach(() => {
    saveAuth({ token: "tok", user });
    setUnauthorizedHandler(onUnauthorized);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    onUnauthorized.mockReset();
  });

  it("sends the bearer token and parses JSON", async () => {
    const fetchMock = respond(200, { ok: 1 });
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiFetch("/x")).resolves.toEqual({ ok: 1 });
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer tok");
  });

  it("returns undefined for 204", async () => {
    vi.stubGlobal("fetch", respond(204));
    await expect(apiFetch("/x", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("logs out and throws ApiError on 401", async () => {
    vi.stubGlobal("fetch", respond(401, { detail: "not authenticated" }));
    const err: ApiError = await apiFetch<never>("/admin/users").catch((e: ApiError) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(401);
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });

  it("does not log out on a 401 from /auth/login", async () => {
    vi.stubGlobal("fetch", respond(401, { detail: "invalid credentials" }));
    await expect(apiFetch("/auth/login", { method: "POST", body: {} })).rejects.toBeInstanceOf(ApiError);
    expect(onUnauthorized).not.toHaveBeenCalled();
  });

  it("keeps the shape of a 422 list and a 409 string", async () => {
    const list = [{ loc: ["body", "username"], msg: "too short" }];
    vi.stubGlobal("fetch", respond(422, { detail: list }));
    await expect(apiFetch("/x")).rejects.toMatchObject({ status: 422, detail: list });

    vi.stubGlobal("fetch", respond(409, { detail: "username already exists" }));
    await expect(apiFetch("/x")).rejects.toMatchObject({ status: 409, detail: "username already exists" });
  });
});
