import { currentToken } from "../auth/session";
import {
  currentApiBase,
  failOverToFallback,
  getApiOrigin,
  resolveApiBase,
} from "./origin";

export interface ValidationItem {
  loc: (string | number)[];
  msg: string;
}

/** FastAPI's `detail`: a message string, or the validation list of a 422. */
export type ErrorDetail = string | ValidationItem[];

export class ApiError extends Error {
  status: number;
  detail: ErrorDetail;

  constructor(status: number, detail: ErrorDetail) {
    super(typeof detail === "string" ? detail : `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

let onUnauthorized: () => void = () => {};

/** Set by AuthProvider: what a 401 does (`logoutLocal`). */
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

interface FetchOptions {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
}

export async function apiFetch<T>(
  path: string,
  { method = "GET", body, signal }: FetchOptions = {},
): Promise<T> {
  const token = currentToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const base = await resolveApiBase();
  const origin = getApiOrigin();
  const canRetry = ["GET", "HEAD"].includes(method.toUpperCase());
  const request = (apiBase: string) =>
    fetch(apiBase + path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  let res: Response;
  try {
    res = await request(base);
  } catch (error) {
    if (origin !== "primary" || !failOverToFallback() || !canRetry)
      throw error;
    res = await request(currentApiBase());
  }
  if (res.status >= 500 && origin === "primary" && failOverToFallback()) {
    if (canRetry) res = await request(currentApiBase());
  }

  if (!res.ok) {
    const data = await res.json().catch(() => null);
    // Only log out if the rejected token is still the current one (another tab may have logged in since).
    if (
      res.status === 401 &&
      path !== "/auth/login" &&
      token &&
      token === currentToken()
    )
      onUnauthorized();
    throw new ApiError(res.status, data?.detail ?? res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
