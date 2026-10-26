import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, use, useCallback, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { useNavigate } from "react-router";
import { apiFetch, setUnauthorizedHandler } from "../api/client";
import { keys } from "../api/keys";
import type { LoginOut, User } from "../api/types";
import {
  AUTH_KEY,
  adoptAuth,
  clearSession,
  currentToken,
  homePath,
  loadAuth,
  parseAuth,
  saveAuth,
  type StoredAuth,
} from "./session";

interface AuthContextValue {
  auth: StoredAuth | null;
  login: (username: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  logoutLocal: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const ctx = use(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const navigateRef = useRef(navigate);
  useLayoutEffect(() => {
    navigateRef.current = navigate;
  }, [navigate]);
  const [auth, setAuth] = useState<StoredAuth | null>(loadAuth);

  const logoutLocal = useCallback(
    (opts?: { keepStorage?: boolean }) => {
      clearSession(queryClient, opts);
      setAuth(null);
      navigateRef.current("/login");
    },
    [queryClient],
  );

  useEffect(() => setUnauthorizedHandler(() => logoutLocal()), [logoutLocal]);

  const login = useCallback(
    async (username: string, password: string) => {
      const res = await apiFetch<LoginOut>("/auth/login", { method: "POST", body: { username, password } });
      clearSession(queryClient, { keepStorage: true });
      saveAuth(res);
      setAuth(res);
      queryClient.setQueryData(keys.me(), res.user);
      return res.user;
    },
    [queryClient],
  );

  const logout = useCallback(async () => {
    await apiFetch("/auth/logout", { method: "POST" }).catch(() => {});
    logoutLocal();
  }, [logoutLocal]);

  // Session restore (frontend-login §2): refresh the stored user in the background.
  useQuery({
    queryKey: keys.me(),
    queryFn: async ({ signal }) => {
      const sentWith = currentToken();
      const fresh = await apiFetch<User>("/auth/me", { signal });
      setAuth((prev) => {
        if (!prev || prev.token !== sentWith) return prev;
        if (prev.user.username === fresh.username && prev.user.display_name === fresh.display_name) return prev;
        const next = { ...prev, user: fresh };
        saveAuth(next);
        return next;
      });
      return fresh;
    },
    enabled: auth !== null,
  });

  // Cross-tab sync (frontend-spec §5.2).
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key !== AUTH_KEY && e.key !== null) return;
      const next = parseAuth(e.newValue);
      const token = currentToken();
      if (!next) {
        if (token) logoutLocal();
        return;
      }
      if (next.token === token) {
        setAuth(next);
        return;
      }
      if (token) logoutLocal({ keepStorage: true });
      adoptAuth(next);
      setAuth(next);
      navigateRef.current(homePath(next.user.role));
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [logoutLocal]);

  return <AuthContext value={{ auth, login, logout, logoutLocal }}>{children}</AuthContext>;
}
