import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router";
import type { Role } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { useEventsStatus } from "../events/EventsProvider";

const NAV: Record<Role, { to: string; label: string }[]> = {
  admin: [
    { to: "/admin/users", label: "Users" },
    { to: "/admin/classes", label: "Classes" },
  ],
  teacher: [
    { to: "/teacher/assignments", label: "Assignments" },
    { to: "/teacher/questions", label: "Questions" },
    { to: "/teacher/generate", label: "Generate" },
  ],
  student: [{ to: "/student", label: "Assignments" }],
};

function ReconnectingBar() {
  const status = useEventsStatus();
  const [late, setLate] = useState(false);
  useEffect(() => {
    if (status !== "reconnecting") return;
    const id = setTimeout(() => setLate(true), 3000);
    return () => {
      clearTimeout(id);
      setLate(false);
    };
  }, [status]);
  if (status !== "reconnecting" || !late) return null;
  return <div className="bg-amber-100 px-4 py-1 text-center text-xs text-amber-800">Reconnecting live updates…</div>;
}

export function Layout() {
  const { auth, logout } = useAuth();
  if (!auth) return null;
  const navClass = ({ isActive }: { isActive: boolean }) =>
    `rounded px-2 py-1 text-sm ${isActive ? "bg-slate-200 font-medium" : "text-slate-600 hover:bg-slate-100"}`;
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-2">
          <span className="font-semibold">CodeIt</span>
          <nav className="flex gap-1">
            {NAV[auth.user.role].map((item) => (
              <NavLink key={item.to} to={item.to} className={navClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>
          <span className="ml-auto text-sm text-slate-600">
            {auth.user.display_name} <span className="text-slate-400">({auth.user.role})</span>
          </span>
          <button type="button" className="btn" onClick={() => void logout()}>
            Log out
          </button>
        </div>
      </header>
      <ReconnectingBar />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
