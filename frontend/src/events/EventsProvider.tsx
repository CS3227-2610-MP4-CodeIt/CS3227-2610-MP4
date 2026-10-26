import { fetchEventSource } from "@microsoft/fetch-event-source";
import { useQueryClient } from "@tanstack/react-query";
import { createContext, use, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { API_BASE } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import { registerStream } from "../auth/session";
import { handleEvent } from "./reconcile";

export type EventsStatus = "connecting" | "open" | "reconnecting";

const EventsContext = createContext<EventsStatus>("connecting");

export const useEventsStatus = () => use(EventsContext);

class FatalAuthError extends Error {}
class RetryableError extends Error {}

const BACKOFF_MS = [1000, 2000, 5000, 10_000, 15_000];

/** The one SSE connection per tab (frontend-spec §4.1). */
export function EventsProvider({ children }: { children: ReactNode }) {
  const { auth, logoutLocal } = useAuth();
  const queryClient = useQueryClient();
  const token = auth?.token ?? null;
  const [status, setStatus] = useState<EventsStatus>("connecting");
  const logoutRef = useRef(logoutLocal);
  useLayoutEffect(() => {
    logoutRef.current = logoutLocal;
  }, [logoutLocal]);

  useEffect(() => {
    if (!token) return;
    const controller = new AbortController();
    const unregister = registerStream(() => controller.abort());
    let attempt = 0;

    fetchEventSource(`${API_BASE}/events`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
      openWhenHidden: false,
      async onopen(res) {
        if (res.status === 401) throw new FatalAuthError();
        if (!res.ok) throw new RetryableError();
        setStatus("open");
      },
      onmessage(msg) {
        if (msg.event === "ready") attempt = 0;
        handleEvent(queryClient, msg);
      },
      onclose() {
        throw new RetryableError();
      },
      onerror(err) {
        if (err instanceof FatalAuthError) throw err;
        setStatus("reconnecting");
        return BACKOFF_MS[Math.min(attempt++, BACKOFF_MS.length - 1)];
      },
    }).catch((err) => {
      if (err instanceof FatalAuthError && !controller.signal.aborted) logoutRef.current();
    });

    return () => {
      unregister();
      controller.abort();
      setStatus("connecting");
    };
  }, [token, queryClient]);

  return <EventsContext value={status}>{children}</EventsContext>;
}
