import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router";
import type { ClassDetail, ClassUpdate, User } from "../../api/types";
import { ConfirmButton } from "../../components/ConfirmButton";
import { formatDate } from "../../components/dates";
import { ErrorText, FieldError } from "../../components/ErrorText";
import { QueryView } from "../../components/QueryView";
import { useAddMembers, useClass, useDeleteClass, useRemoveMember, useUpdateClass, useUsers } from "./api";

export function ClassPage() {
  const id = Number(useParams().id);
  const cls = useClass(id);
  return <QueryView query={cls}>{(c) => <ClassDetailView cls={c} />}</QueryView>;
}

function ClassDetailView({ cls }: { cls: ClassDetail }) {
  const navigate = useNavigate();
  const remove = useDeleteClass(cls.id);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/admin/classes" className="link text-sm">← Classes</Link>
        <h1 className="text-xl font-semibold">{cls.name}</h1>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Classes have no updated_at; keying on the editable fields remounts the form after a save. */}
        <EditClassForm key={`${cls.id}:${cls.name}:${cls.description}`} cls={cls} />
        <AssignmentsCard cls={cls} />
        <MembersCard cls={cls} title="Teachers" members={cls.teachers} />
        <MembersCard cls={cls} title="Students" members={cls.students} />
      </div>
      <AddMembers cls={cls} />
      <div className="card space-y-2">
        <h2 className="font-medium">Delete class</h2>
        <p className="text-sm text-slate-600">Removes its memberships, assignments and their submissions.</p>
        <ConfirmButton
          message={`Delete class ${cls.name}?`}
          disabled={remove.isPending}
          onConfirm={() => remove.mutate(undefined, { onSuccess: () => navigate("/admin/classes") })}
        >
          Delete
        </ConfirmButton>
        <ErrorText error={remove.error} />
      </div>
    </div>
  );
}

function EditClassForm({ cls }: { cls: ClassDetail }) {
  const update = useUpdateClass(cls.id);
  const [name, setName] = useState(cls.name);
  const [description, setDescription] = useState(cls.description);

  const body: ClassUpdate = {};
  if (name !== cls.name) body.name = name;
  if (description !== cls.description) body.description = description;
  const changed = Object.keys(body).length > 0;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    update.mutate(body);
  };

  return (
    <form onSubmit={onSubmit} className="card space-y-3">
      <h2 className="font-medium">Edit</h2>
      <div>
        <label className="label" htmlFor="class-name">Name</label>
        <input id="class-name" className="input" value={name} onChange={(e) => setName(e.target.value)} />
        <FieldError error={update.error} field="name" />
      </div>
      <div>
        <label className="label" htmlFor="class-desc">Description</label>
        <textarea
          id="class-desc"
          className="input"
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <FieldError error={update.error} field="description" />
      </div>
      <ErrorText error={update.error} fields={["name", "description"]} messages={{ 409: "Class name already taken" }} />
      <button type="submit" className="btn btn-primary" disabled={update.isPending || !changed || !name.trim()}>
        Save
      </button>
    </form>
  );
}

function AssignmentsCard({ cls }: { cls: ClassDetail }) {
  return (
    <div className="card space-y-3 self-start">
      <h2 className="font-medium">Assignments</h2>
      {cls.assignments.length === 0 ? (
        <p className="text-sm text-slate-500">No assignments yet.</p>
      ) : (
        <ul className="space-y-1 text-sm">
          {cls.assignments.map((a) => (
            <li key={a.id} className="flex justify-between gap-2">
              <Link to={`/admin/classes/${cls.id}/assignments/${a.id}`} className="link">{a.title}</Link>
              <span className="text-slate-500">{a.due_at ? `due ${formatDate(a.due_at)}` : "no due date"}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function MembersCard({ cls, title, members }: { cls: ClassDetail; title: string; members: User[] }) {
  const remove = useRemoveMember(cls.id);
  return (
    <div className="card space-y-3 self-start">
      <h2 className="font-medium">
        {title} <span className="text-slate-400">({members.length})</span>
      </h2>
      {members.length === 0 ? (
        <p className="text-sm text-slate-500">None.</p>
      ) : (
        <ul className="divide-y divide-slate-100 text-sm">
          {members.map((m) => (
            <li key={m.id} className="flex items-center justify-between py-1">
              <Link to={`/admin/users/${m.id}`} className="link">
                {m.display_name} <span className="text-slate-400">@{m.username}</span>
              </Link>
              <button
                type="button"
                className="btn btn-danger px-2 py-0.5 text-xs"
                disabled={remove.isPending}
                onClick={() => remove.mutate(m.id)}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
      <ErrorText error={remove.error} />
    </div>
  );
}

/** Multi-select of teachers and students who are not members yet, filtered by a search box. */
function AddMembers({ cls }: { cls: ClassDetail }) {
  const users = useUsers();
  const add = useAddMembers(cls.id);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<number>>(new Set());

  const memberIds = new Set([...cls.teachers, ...cls.students].map((m) => m.id));
  const q = search.trim().toLowerCase();
  const candidates = (users.data ?? []).filter(
    (u) =>
      u.role !== "admin" &&
      !memberIds.has(u.id) &&
      (!q || u.username.toLowerCase().includes(q) || u.display_name.toLowerCase().includes(q)),
  );
  // Drop selections that became members (e.g. added from another tab).
  const chosen = [...selected].filter((id) => !memberIds.has(id));

  const toggle = (id: number) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  return (
    <div className="card space-y-3">
      <h2 className="font-medium">Add members</h2>
      <input
        className="input"
        placeholder="Search by username or name"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      {users.isPending ? (
        <p className="text-sm text-slate-500">Loading users…</p>
      ) : users.isError ? (
        <ErrorText error={users.error} onRetry={() => void users.refetch()} />
      ) : candidates.length === 0 ? (
        <p className="text-sm text-slate-500">No matching users to add.</p>
      ) : (
        <ul className="max-h-64 overflow-y-auto rounded border border-slate-200 text-sm">
          {candidates.map((u) => (
            <li key={u.id}>
              <label className="flex cursor-pointer items-center gap-2 px-2 py-1 hover:bg-slate-50">
                <input type="checkbox" checked={selected.has(u.id)} onChange={() => toggle(u.id)} />
                {u.display_name} <span className="text-slate-400">@{u.username}</span>
                <span className="ml-auto text-xs text-slate-500">{u.role}</span>
              </label>
            </li>
          ))}
        </ul>
      )}
      <ErrorText error={add.error} />
      <button
        type="button"
        className="btn btn-primary"
        disabled={add.isPending || chosen.length === 0}
        onClick={() => add.mutate(chosen, { onSuccess: () => setSelected(new Set()) })}
      >
        Add {chosen.length || ""} selected
      </button>
    </div>
  );
}
