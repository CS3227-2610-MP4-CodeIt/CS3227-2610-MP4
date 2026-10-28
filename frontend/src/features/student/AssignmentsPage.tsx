import { Link } from "react-router";
import type { StudentAssignment } from "../../api/types";
import { formatDate } from "../../components/dates";
import { QueryView } from "../../components/QueryView";
import { useStudentAssignments } from "./api";
import { isPastDue } from "./verdict";

/** Group by class, keeping the backend's order within each class. */
function byClass(list: StudentAssignment[]) {
  const groups = new Map<number, { name: string; assignments: StudentAssignment[] }>();
  for (const a of list) {
    const g = groups.get(a.class_id) ?? { name: a.class_name, assignments: [] };
    g.assignments.push(a);
    groups.set(a.class_id, g);
  }
  return [...groups.entries()].sort(([, x], [, y]) => x.name.localeCompare(y.name));
}

export function AssignmentsPage() {
  const assignments = useStudentAssignments();
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Assignments</h1>
      <QueryView query={assignments}>
        {(list) =>
          list.length === 0 ? (
            <p className="text-sm text-slate-500">No assignments yet.</p>
          ) : (
            byClass(list).map(([classId, g]) => (
              <section key={classId} className="card space-y-2 overflow-x-auto">
                <h2 className="font-medium">{g.name}</h2>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Due</th>
                      <th>Solved</th>
                    </tr>
                  </thead>
                  <tbody>
                    {g.assignments.map((a) => (
                      <tr key={a.id}>
                        <td>
                          <Link to={`/student/assignments/${a.id}`} className="link">{a.title}</Link>
                        </td>
                        <td><DueDate dueAt={a.due_at} /></td>
                        <td>
                          {a.questions.filter((q) => q.solved).length} / {a.questions.length}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>
            ))
          )
        }
      </QueryView>
    </div>
  );
}

export function DueDate({ dueAt }: { dueAt: string | null }) {
  if (!dueAt) return <span className="text-slate-400">none</span>;
  return (
    <>
      {formatDate(dueAt)}
      {isPastDue(dueAt) && <span className="ml-2 rounded bg-slate-200 px-1.5 text-xs text-slate-600">closed</span>}
    </>
  );
}
