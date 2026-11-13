import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router";
import { ApiError } from "../../api/client";
import type { Role } from "../../api/types";
import { useAuth } from "../../auth/AuthProvider";
import { homePath } from "../../auth/session";
import { ErrorText } from "../../components/ErrorText";
import { PasswordInput } from "../../components/PasswordInput";

/** `?next=` is only followed when it is a path under the user's own role. */
function nextPath(next: string | null, role: Role): string {
  const home = homePath(role);
  if (
    next &&
    (next === home ||
      next.startsWith(`${home}/`) ||
      next.startsWith(`${home}?`))
  )
    return next;
  return home;
}

export function LoginPage() {
  const { auth, login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: () => login(username, password),
    onSuccess: (user) =>
      navigate(nextPath(params.get("next"), user.role), { replace: true }),
    onError: (err) => {
      if (err instanceof ApiError && err.status === 401) setPassword("");
    },
  });

  if (auth && !mutation.isPending)
    return <Navigate to={homePath(auth.user.role)} replace />;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-6">
      <div className="grid w-full max-w-[720px] overflow-hidden rounded border border-slate-200 bg-white sm:grid-cols-[minmax(150px,0.74fr)_minmax(0,1.26fr)]">
        <aside className="flex flex-col gap-4 bg-blue-50 p-4 sm:gap-5 sm:p-6">
          <div className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className="grid h-6 w-6 place-items-center rounded bg-blue-600 text-[13px] font-bold text-white"
            >
              C
            </span>
            <p className="text-sm font-semibold text-blue-700">CodeIt</p>
          </div>
          <p className="text-lg font-semibold leading-tight text-slate-900 sm:my-auto sm:max-w-[13ch] sm:text-xl">
            Your programming coursework, in one place.
          </p>
        </aside>
        <form
          aria-busy={mutation.isPending}
          onSubmit={onSubmit}
          className="min-w-0 space-y-4 p-[18px] sm:p-[22px]"
        >
          <div>
            <h1 className="text-2xl font-semibold">Log in</h1>
            <p className="mt-1 text-sm text-slate-600">
              Use the account provided by your course administrator.
            </p>
          </div>
          <div>
            <label className="label" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              className="input"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="password">
              Password
            </label>
            <PasswordInput
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary w-full justify-center"
            disabled={mutation.isPending || !username || !password}
          >
            {mutation.isPending ? "Logging in…" : "Log in"}
          </button>
          <div className="min-h-10">
            <p role="status" className="text-sm text-slate-600">
              {mutation.isPending ? "Logging in…" : ""}
            </p>
            <ErrorText
              error={mutation.error}
              messages={{ 401: "Invalid username or password." }}
            />
          </div>
        </form>
      </div>
    </main>
  );
}
