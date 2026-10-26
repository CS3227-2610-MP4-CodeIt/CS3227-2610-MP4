import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import type { Role } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { homePath } from "../auth/session";

/** UX-only guard; the backend checks every call anyway (frontend-spec §7). */
export function RequireRole({ role, children }: { role: Role; children: ReactNode }) {
  const { auth } = useAuth();
  const location = useLocation();
  if (!auth) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }
  if (auth.user.role !== role) return <Navigate to={homePath(auth.user.role)} replace />;
  return children;
}
