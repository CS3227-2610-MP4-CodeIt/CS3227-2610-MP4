import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router";
import type { UserDetail, UserUpdate } from "../../api/types";
import { useAuth } from "../../auth/AuthProvider";
import { ConfirmButton } from "../../components/ConfirmButton";
import { ErrorText, FieldError } from "../../components/ErrorText";
import { PasswordInput } from "../../components/PasswordInput";
import { QueryView } from "../../components/QueryView";
import { useDeleteUser, useUpdateUser, useUser } from "./api";

export function UserPage() {
  const id = Number(useParams().id);
  const user = useUser(id);
  return <QueryView query={user}>{(u) => <UserDetailView user={u} />}</QueryView>;
}

function UserDetailView({ user }: { user: UserDetail }) {
  const navigate = useNavigate();
  const remove = useDeleteUser(user.id);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/admin/users" className="link text-sm">← Users</Link>
        <h1 className="text-xl font-semibold">{user.display_name}</h1>
        <span className="text-sm text-slate-500">{user.role}</span>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Users have no updated_at; keying on the editable fields remounts the form after a save. */}
        <EditUserForm key={`${user.id}:${user.username}:${user.display_name}`} user={user} />
        <div className="card space-y-3 self-start">
          <h2 className="font-medium">Classes</h2>
          {user.classes.length === 0 ? (
            <p className="text-sm text-slate-500">Not in any class.</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {user.classes.map((c) => (
                <li key={c.id}>
                  <Link to={`/admin/classes/${c.id}`} className="link">{c.name}</Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      <div className="card space-y-2">
        <h2 className="font-medium">Delete user</h2>
        <p className="text-sm text-slate-600">
          Removes their sessions, class memberships, submissions and jobs. Questions and assignments they made stay.
        </p>
        <ConfirmButton
          message={`Delete user ${user.username}?`}
          disabled={remove.isPending}
          onConfirm={() => remove.mutate(undefined, { onSuccess: () => navigate("/admin/users") })}
        >
          Delete
        </ConfirmButton>
        <ErrorText error={remove.error} />
      </div>
    </div>
  );
}

function EditUserForm({ user }: { user: UserDetail }) {
  const { auth } = useAuth();
  const update = useUpdateUser(user.id);
  const [username, setUsername] = useState(user.username);
  const [displayName, setDisplayName] = useState(user.display_name);
  const [password, setPassword] = useState("");
  const isSelf = auth?.user.id === user.id;

  // Only changed fields are sent; a blank password means unchanged.
  const body: UserUpdate = {};
  if (username !== user.username) body.username = username;
  if (displayName !== user.display_name) body.display_name = displayName;
  if (password) body.password = password;
  const changed = Object.keys(body).length > 0;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    update.mutate(body, { onSuccess: () => setPassword("") });
  };

  return (
    <form onSubmit={onSubmit} className="card space-y-3">
      <h2 className="font-medium">Edit</h2>
      <div>
        <label className="label" htmlFor="edit-username">Username</label>
        <input id="edit-username" className="input" value={username} onChange={(e) => setUsername(e.target.value)} />
        <FieldError error={update.error} field="username" />
      </div>
      <div>
        <label className="label" htmlFor="edit-display">Display name</label>
        <input id="edit-display" className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
        <FieldError error={update.error} field="display_name" />
      </div>
      <div>
        <label className="label" htmlFor="edit-password">New password</label>
        <PasswordInput
          id="edit-password"
          autoComplete="new-password"
          placeholder="Leave blank to keep the current password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <FieldError error={update.error} field="password" />
        <p className="mt-1 text-xs text-slate-500">
          {isSelf
            ? "Changing your own password logs you out."
            : "Changing the password logs this user out of all sessions."}
        </p>
      </div>
      <ErrorText
        error={update.error}
        fields={["username", "display_name", "password"]}
        messages={{ 409: "Username already taken" }}
      />
      <button type="submit" className="btn btn-primary" disabled={update.isPending || !changed}>
        Save
      </button>
    </form>
  );
}
