const primary = apiOrigin(import.meta.env.VITE_API_BASE_URL ?? "");
const fallback = apiOrigin(import.meta.env.VITE_API_FALLBACK_URL ?? "");

export type ApiOrigin = "primary" | "fallback";

let activeOrigin: ApiOrigin = "primary";
let initialCheck: Promise<void> | undefined;
const listeners = new Set<() => void>();

function apiOrigin(value: string): string {
  const trimmed = value.trim().replace(/\/$/, "");
  if (!trimmed) return "";
  const url = new URL(trimmed);
  if (
    !["http:", "https:"].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  ) {
    throw new Error("API URLs must be trusted HTTP(S) origins without a path");
  }
  if (import.meta.env.PROD && url.protocol !== "https:") {
    throw new Error("Production API origins must use HTTPS");
  }
  return url.origin;
}

export function getApiOrigin(): ApiOrigin {
  return activeOrigin;
}

export function subscribeApiOrigin(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function chooseFallback(): boolean {
  if (!fallback || activeOrigin === "fallback") return false;
  activeOrigin = "fallback";
  for (const listener of listeners) listener();
  return true;
}

async function probe(origin: string): Promise<boolean> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 2500);
  try {
    const response = await fetch(`${origin}/api/health/ready`, {
      signal: controller.signal,
      cache: "no-store",
    });
    return response.ok;
  } catch {
    return false;
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function resolveApiBase(): Promise<string> {
  if (activeOrigin === "primary" && fallback) {
    initialCheck ??= (async () => {
      if (!(await probe(primary))) chooseFallback();
    })();
    await initialCheck;
  }
  return `${activeOrigin === "fallback" ? fallback : primary}/api`;
}

export function currentApiBase(): string {
  return `${activeOrigin === "fallback" ? fallback : primary}/api`;
}

export function failOverToFallback(): boolean {
  return chooseFallback();
}

export function hasApiFallback(): boolean {
  return Boolean(fallback);
}
