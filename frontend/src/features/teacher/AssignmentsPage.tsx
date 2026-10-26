import { Link, useSearchParams } from "react-router";
import { useAuth } from "../../auth/AuthProvider";
import { formatDate } from "../../components/dates";
import { QueryView } from "../../components/QueryView";
import { useAssignments, useTeacherClasses } from "./api";

export function AssignmentsPage() {
  const { auth } = useAuth();
  const [params, setParams] = useSearchParams();
  const raw = Number(params.get("class_id"));
  const classId = Number.isInteger(raw) && raw > 0 ? raw : undefined;
  const classes = useTeacherClasses();
  const assignments = useAssignments(classId);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-4">
        <h1 className="text-xl font-semibold">Assignments</h1>
        <select
          className="input w-auto"
          value={classId ?? ""}
          onChange={(e) => setParams(e.target.value ? { class_id: e.target.value } : {})}
          aria-label="Class"
        >
          <option value="">All my classes</option>
          {classes.data?.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <Link
          to={classId ? `/teacher/assignments/new?class_id=${classId}` : "/teacher/assignments/new"}
          className="btn btn-primary ml-auto"
        >
          New assignment
        </Link>
      </div>
      <div className="card overflow-x-auto">
        <QueryView query={assignments}>
          {(list) =>
            list.length === 0 ? (
              <p className="text-sm text-slate-500">No assignments.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Class</th>
                    <th>Due</th>
                    <th>Questions</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((a) => (
                    <tr key={a.id}>
                      <td>
                        <Link to={`/teacher/assignments/${a.id}`} className="link">{a.title}</Link>
                        {a.created_by === auth?.user.id && <span className="ml-2 text-xs text-slate-400">yours</span>}
                      </td>
                      <td>{a.class_name}</td>
                      <td>{a.due_at ? formatDate(a.due_at) : <span className="text-slate-400">none</span>}</td>
                      <td>{a.questions.length}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          }
        </QueryView>
      </div>
    </div>
  );
}
