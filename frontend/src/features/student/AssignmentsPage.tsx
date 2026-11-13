import { Link } from "react-router";
import type { StudentAssignment } from "../../api/types";
import { formatDate } from "../../components/dates";
import { QueryView } from "../../components/QueryView";
import { useStudentAssignments } from "./api";
import { isPastDue } from "./verdict";

function byClass(list: StudentAssignment[]) {
  const groups = new Map<
    number,
    { name: string; assignments: StudentAssignment[] }
  >();
  for (const a of list) {
    const g = groups.get(a.class_id) ?? { name: a.class_name, assignments: [] };
    g.assignments.push(a);
    groups.set(a.class_id, g);
  }
  return [...groups.entries()].sort(([, x], [, y]) =>
    x.name.localeCompare(y.name),
  );
}

export function AssignmentsPage() {
  const assignments = useStudentAssignments();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Assignments</h1>
        <p className="mt-2 text-sm text-slate-600">
          Your coursework, organized by class.
        </p>
      </div>
      <QueryView query={assignments}>
        {(list) =>
          list.length === 0 ? (
            <p className="text-sm text-slate-500">
              No assignments yet. Check back when your teacher has assigned
              work.
            </p>
          ) : (
            byClass(list).map(([classId, g]) => (
              <section
                key={classId}
                className="overflow-hidden rounded border border-slate-200 bg-white"
              >
                <header className="flex flex-wrap items-baseline justify-between gap-2 border-b border-slate-200 px-5 py-4">
                  <h2 className="break-words font-semibold">{g.name}</h2>
                  <span className="text-sm text-slate-500">
                    {g.assignments.length}{" "}
                    {g.assignments.length === 1 ? "assignment" : "assignments"}
                  </span>
                </header>
                <ul className="divide-y divide-slate-100">
                  {g.assignments.map((a) => {
                    const solved = a.questions.filter((q) => q.solved).length;
                    const total = a.questions.length;
                    return (
                      <li
                        key={a.id}
                        className="grid gap-2 px-5 py-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,0.6fr)_minmax(0,0.6fr)] sm:gap-5"
                      >
                        <div className="min-w-0 break-words">
                          <Link
                            to={`/student/assignments/${a.id}`}
                            className="link font-semibold"
                          >
                            {a.title}
                          </Link>
                          <p className="mt-1 text-sm text-slate-500">
                            {a.questions.length}{" "}
                            {a.questions.length === 1
                              ? "question"
                              : "questions"}
                          </p>
                        </div>
                        <p className="text-sm text-slate-600">
                          <DueDate dueAt={a.due_at} />
                        </p>
                        <div className="text-sm text-slate-700">
                          <p className="font-medium">
                            {solved} of {total} solved
                          </p>
                          {total > 0 && solved > 0 && (
                            <span
                              className={`mt-1 inline-block rounded px-2 py-0.5 text-xs ${solved === total ? "bg-green-50 text-green-700" : "bg-blue-50 text-blue-700"}`}
                            >
                              {solved === total ? "Completed" : "In progress"}
                            </span>
                          )}
                          <ProgressBar solved={solved} total={total} />
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </section>
            ))
          )
        }
      </QueryView>
    </div>
  );
}

export function DueDate({ dueAt }: { dueAt: string | null }) {
  if (!dueAt) return <span>No due date</span>;
  return (
    <>
      <span>Due {formatDate(dueAt)}</span>
      {isPastDue(dueAt) && (
        <span className="ml-2 rounded bg-slate-200 px-1.5 text-xs text-slate-600">
          closed
        </span>
      )}
    </>
  );
}

/** Decorative track; the adjacent text exposes the count to all users. */
export function ProgressBar({
  solved,
  total,
}: {
  solved: number;
  total: number;
}) {
  const percent =
    total > 0 ? Math.min(100, Math.max(0, (solved / total) * 100)) : 0;
  return (
    <div
      aria-hidden="true"
      className="mt-2 h-1 w-full max-w-32 overflow-hidden rounded bg-slate-200"
    >
      <div
        className="h-full rounded bg-blue-600"
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}
