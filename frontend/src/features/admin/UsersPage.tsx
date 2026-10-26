import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router";
import type { MemberRole, Role } from "../../api/types";
import { ErrorText, FieldError } from "../../components/ErrorText";
import { PasswordInput } from "../../components/PasswordInput";
import { QueryView } from "../../components/QueryView";
import { useCreateUser, useUsers } from "./api";

const ROLES: Role[] = ["teacher", "student", "admin"];
const isRole = (v: string | null): v is Role => ROLES.includes(v as Role);

export function UsersPage() {
  const [params, setParams] = useSearchParams();
  const raw = params.get("role");
  const role = isRole(raw) ? raw : undefined;
  const users = useUsers(role);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold">Users</h1>
        <select
          className="input w-auto"
          value={role ?? ""}
          onChange={(e) => setParams(e.target.value ? { role: e.target.value } : {})}
        >
          <option value="">All roles</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>
      <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
        <div className="card overflow-x-auto">
          <QueryView query={users}>
            {(list) =>
              list.length === 0 ? (
                <p className="text-sm text-slate-500">No users.</p>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Username</th>
                      <th>Display name</th>
                      <th>Role</th>
                    </tr>
                  </thead>
                  <tbody>
                    {list.map((u) => (
                      <tr key={u.id}>
                        <td>
                          <Link to={`/admin/users/${u.id}`} className="link">
                            {u.username}
                          </Link>
                        </td>
                        <td>{u.display_name}</td>
                        <td>{u.role}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
            }
          </QueryView>
        </div>
        <NewUserForm />
      </div>
    </div>
  );
}

function NewUserForm() {
  const create = useCreateUser();
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<MemberRole>("student");

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    create.mutate(
      { username, display_name: displayName, password, role },
      {
        onSuccess: () => {
          setUsername("");
          setDisplayName("");
          setPassword("");
        },
      },
    );
  };

  return (
    <form onSubmit={onSubmit} className="card space-y-3 self-start">
      <h2 className="font-medium">New user</h2>
      <div>
        <label className="label" htmlFor="new-username">Username</label>
        <input id="new-username" className="input" value={username} onChange={(e) => setUsername(e.target.value)} />
        <FieldError error={create.error} field="username" />
      </div>
      <div>
        <label className="label" htmlFor="new-display">Display name</label>
        <input id="new-display" className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
        <FieldError error={create.error} field="display_name" />
      </div>
      <div>
        <label className="label" htmlFor="new-password">Password</label>
        <PasswordInput
          id="new-password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <FieldError error={create.error} field="password" />
      </div>
      <div>
        <label className="label" htmlFor="new-role">Role</label>
        <select id="new-role" className="input" value={role} onChange={(e) => setRole(e.target.value as MemberRole)}>
          <option value="student">student</option>
          <option value="teacher">teacher</option>
        </select>
      </div>
      <ErrorText
        error={create.error}
        fields={["username", "display_name", "password", "role"]}
        messages={{ 409: "Username already taken" }}
      />
      <button
        type="submit"
        className="btn btn-primary"
        disabled={create.isPending || !username || !displayName || !password}
      >
        Create user
      </button>
    </form>
  );
}
