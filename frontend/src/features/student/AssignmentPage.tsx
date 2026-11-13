import { formatDifficulty } from "../../components/difficulty";
import { Link, useParams } from "react-router";
import { Markdown } from "../../components/Markdown";
import { QueryView } from "../../components/QueryView";
import { useStudentAssignment } from "./api";
import { DueDate, ProgressBar } from "./AssignmentsPage";

export function AssignmentPage() {
  const aid = Number(useParams().aid);
  const assignment = useStudentAssignment(aid);
  return (
    <QueryView query={assignment}>
      {(a) => {
        const solved = a.questions.filter((q) => q.solved).length;
        return (
          <div className="space-y-6">
            <header className="space-y-3 border-b border-slate-200 pb-5">
              <Link to="/student" className="link text-sm">
                ← Assignments
              </Link>
              <h1 className="break-words text-2xl font-semibold">{a.title}</h1>
              <p className="break-words text-sm text-slate-600">
                {a.class_name} · <DueDate dueAt={a.due_at} />
              </p>
            </header>
            <div className="grid items-start gap-5 md:grid-cols-[minmax(0,1fr)_230px]">
              <div className="min-w-0 space-y-5">
                {a.description_md && (
                  <section className="card min-w-0 break-words">
                    <h2 className="mb-3 font-semibold">
                      About this assignment
                    </h2>
                    <Markdown>{a.description_md}</Markdown>
                  </section>
                )}
                <section className="card min-w-0">
                  <h2 className="font-semibold">Questions</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Choose a question to view its problem and editor.
                  </p>
                  <ol className="mt-4 divide-y divide-slate-100 border-t border-slate-200">
                    {a.questions.map((q) => (
                      <li
                        key={q.id}
                        className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-2 py-4 sm:grid-cols-[2rem_minmax(0,1fr)_auto]"
                      >
                        <span className="text-sm text-slate-500">
                          {q.position}
                        </span>
                        <div className="min-w-0 break-words">
                          <Link
                            to={`/student/assignments/${a.id}/questions/${q.id}`}
                            className="link font-semibold"
                          >
                            {q.title}
                          </Link>
                          <p className="mt-1 text-sm text-slate-500">
                            {formatDifficulty(q.difficulty)}
                          </p>
                        </div>
                        <span
                          className={`col-start-2 w-fit self-center rounded px-2 py-1 text-xs sm:col-start-auto ${q.solved ? "bg-green-50 text-green-700" : "bg-slate-100 text-slate-700"}`}
                        >
                          {q.solved ? "Solved" : "Not solved"}
                        </span>
                      </li>
                    ))}
                  </ol>
                </section>
              </div>
              <aside className="rounded border border-slate-200 bg-slate-100 p-5">
                <h2 className="font-semibold">Your progress</h2>
                <p className="mt-3 text-2xl font-semibold">
                  {solved} / {a.questions.length}
                </p>
                <p className="text-sm text-slate-600">questions solved</p>
                <ProgressBar solved={solved} total={a.questions.length} />
              </aside>
            </div>
          </div>
        );
      }}
    </QueryView>
  );
}
