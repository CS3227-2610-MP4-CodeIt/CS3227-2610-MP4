import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { ErrorText, FieldError } from "../../components/ErrorText";
import { QueryView } from "../../components/QueryView";
import { useClasses, useCreateClass } from "./api";

export function ClassesPage() {
  const classes = useClasses();
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Classes</h1>
      <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
        <div className="card overflow-x-auto">
          <QueryView query={classes}>
            {(list) =>
              list.length === 0 ? (
                <p className="text-sm text-slate-500">No classes yet.</p>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Teachers</th>
                      <th>Students</th>
                    </tr>
                  </thead>
                  <tbody>
                    {list.map((c) => (
                      <tr key={c.id}>
                        <td>
                          <Link to={`/admin/classes/${c.id}`} className="link">{c.name}</Link>
                        </td>
                        <td>{c.teacher_count}</td>
                        <td>{c.student_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
            }
          </QueryView>
        </div>
        <NewClassForm />
      </div>
    </div>
  );
}

function NewClassForm() {
  const navigate = useNavigate();
  const create = useCreateClass();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    create.mutate({ name, description }, { onSuccess: (cls) => navigate(`/admin/classes/${cls.id}`) });
  };

  return (
    <form onSubmit={onSubmit} className="card space-y-3 self-start">
      <h2 className="font-medium">New class</h2>
      <div>
        <label className="label" htmlFor="new-class-name">Name</label>
        <input id="new-class-name" className="input" value={name} onChange={(e) => setName(e.target.value)} />
        <FieldError error={create.error} field="name" />
      </div>
      <div>
        <label className="label" htmlFor="new-class-desc">Description</label>
        <textarea
          id="new-class-desc"
          className="input"
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <FieldError error={create.error} field="description" />
      </div>
      <ErrorText error={create.error} fields={["name", "description"]} messages={{ 409: "Class name already taken" }} />
      <button type="submit" className="btn btn-primary" disabled={create.isPending || !name.trim()}>
        Create class
      </button>
    </form>
  );
}
