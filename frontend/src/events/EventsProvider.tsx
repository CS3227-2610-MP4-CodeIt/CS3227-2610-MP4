import { fetchEventSource } from "@microsoft/fetch-event-source";
import { useQueryClient } from "@tanstack/react-query";
import {
  createContext,
  use,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import {
  failOverToFallback,
  getApiOrigin,
  resolveApiBase,
  subscribeApiOrigin,
} from "../api/origin";
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
  const origin = useSyncExternalStore(
    subscribeApiOrigin,
    getApiOrigin,
    getApiOrigin,
  );
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

    let disposed = false;
    void resolveApiBase().then((base) => {
      if (disposed) return;
      fetchEventSource(`${base}/events`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
        openWhenHidden: false,
        async onopen(res) {
          if (res.status === 401) throw new FatalAuthError();
          if (res.status >= 500 && origin === "primary") failOverToFallback();
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
          if (!(err instanceof RetryableError) && origin === "primary")
            failOverToFallback();
          setStatus("reconnecting");
          return BACKOFF_MS[Math.min(attempt++, BACKOFF_MS.length - 1)];
        },
      }).catch((err) => {
        if (err instanceof FatalAuthError && !controller.signal.aborted)
          logoutRef.current();
      });
    });

    return () => {
      unregister();
      disposed = true;
      controller.abort();
      setStatus("connecting");
    };
  }, [token, queryClient, origin]);

  return <EventsContext value={status}>{children}</EventsContext>;
}
