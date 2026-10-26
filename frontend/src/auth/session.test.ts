import { QueryClient } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AUTH_KEY, clearSession, currentToken, loadAuth, registerStream, saveAuth } from "./session";

function fakeStorage() {
  const data = new Map<string, string>();
  return {
    getItem: (k: string) => data.get(k) ?? null,
    setItem: (k: string, v: string) => void data.set(k, v),
    removeItem: (k: string) => void data.delete(k),
  };
}

const auth = { token: "tok", user: { id: 1, username: "a", display_name: "A", role: "admin" as const } };

describe("session", () => {
  beforeEach(() => vi.stubGlobal("localStorage", fakeStorage()));
  afterEach(() => vi.unstubAllGlobals());

  it("logoutLocal aborts the stream before clearing the cache, then removes stored auth", () => {
    saveAuth(auth);
    const calls: string[] = [];
    registerStream(() => calls.push("abort"));
    const qc = new QueryClient();
    qc.setQueryData(["me"], auth.user);
    const clear = qc.clear.bind(qc);
    vi.spyOn(qc, "clear").mockImplementation(() => {
      calls.push("clear");
      clear();
    });

    clearSession(qc);

    expect(calls).toEqual(["abort", "clear"]);
    expect(qc.getQueryData(["me"])).toBeUndefined();
    expect(localStorage.getItem(AUTH_KEY)).toBeNull();
    expect(currentToken()).toBeNull();
  });

  it("keepStorage leaves another tab's login in storage", () => {
    saveAuth(auth);
    clearSession(new QueryClient(), { keepStorage: true });
    expect(localStorage.getItem(AUTH_KEY)).not.toBeNull();
  });

  it("loadAuth restores a stored login and ignores a corrupt one", () => {
    saveAuth(auth);
    expect(loadAuth()).toEqual(auth);
    expect(currentToken()).toBe("tok");
    localStorage.setItem(AUTH_KEY, "{bad");
    expect(loadAuth()).toBeNull();
    expect(currentToken()).toBeNull();
  });
});
