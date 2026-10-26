import type { QueryClient } from "@tanstack/react-query";
import type { LoginOut, Role } from "../api/types";

// Auth storage and the logout steps (frontend-spec §5), kept free of React so they can be unit-tested.

export type StoredAuth = LoginOut;

export const AUTH_KEY = "auth";

// In-memory copy of the token, read synchronously by apiFetch.
let token: string | null = null;
// Aborts the current SSE stream; registered by EventsProvider.
let abortStream: (() => void) | null = null;

export const currentToken = () => token;

export const homePath = (role: Role) => `/${role}`;

export function parseAuth(raw: string | null): StoredAuth | null {
  if (!raw) return null;
  try {
    const value = JSON.parse(raw);
    if (typeof value?.token === "string" && typeof value?.user?.role === "string") return value;
  } catch {
    // corrupt entry: treat as logged out
  }
  return null;
}

/** App start: read `localStorage["auth"]` and adopt it. */
export function loadAuth(): StoredAuth | null {
  let auth: StoredAuth | null = null;
  try {
    auth = parseAuth(localStorage.getItem(AUTH_KEY));
  } catch {
    // storage unavailable
  }
  token = auth?.token ?? null;
  return auth;
}

/** Use an auth another tab already stored, without writing it back. */
export function adoptAuth(auth: StoredAuth) {
  token = auth.token;
}

export function saveAuth(auth: StoredAuth) {
  token = auth.token;
  try {
    localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
  } catch {
    // storage unavailable: the login lasts until the tab closes
  }
}

/** Returns an unregister function that only clears the slot if it still holds `fn`. */
export function registerStream(fn: () => void): () => void {
  abortStream = fn;
  return () => {
    if (abortStream === fn) abortStream = null;
  };
}

/**
 * Steps 1–3 of `logoutLocal()` (frontend-spec §5.2), in this order: abort the stream, clear the
 * cache, remove the stored auth. `keepStorage` is for a cross-tab switch, where storage already
 * holds the other tab's new login.
 */
export function clearSession(queryClient: QueryClient, { keepStorage = false } = {}) {
  abortStream?.();
  abortStream = null;
  queryClient.clear();
  token = null;
  if (keepStorage) return;
  try {
    localStorage.removeItem(AUTH_KEY);
  } catch {
    // storage unavailable
  }
}
