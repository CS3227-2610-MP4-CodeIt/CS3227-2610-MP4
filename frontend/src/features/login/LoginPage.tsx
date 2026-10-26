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
  if (next && (next === home || next.startsWith(`${home}/`) || next.startsWith(`${home}?`))) return next;
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
    onSuccess: (user) => navigate(nextPath(params.get("next"), user.role), { replace: true }),
    onError: (err) => {
      if (err instanceof ApiError && err.status === 401) setPassword("");
    },
  });

  if (auth && !mutation.isPending) return <Navigate to={homePath(auth.user.role)} replace />;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={onSubmit} className="card w-full max-w-sm space-y-4">
        <h1 className="text-lg font-semibold">Log in</h1>
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
        <ErrorText error={mutation.error} messages={{ 401: "Invalid username or password." }} />
        <button
          type="submit"
          className="btn btn-primary w-full justify-center"
          disabled={mutation.isPending || !username || !password}
        >
          Log in
        </button>
      </form>
    </div>
  );
}
