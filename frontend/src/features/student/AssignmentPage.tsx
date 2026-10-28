import { Link, useParams } from "react-router";
import { Markdown } from "../../components/Markdown";
import { QueryView } from "../../components/QueryView";
import { useStudentAssignment } from "./api";
import { DueDate } from "./AssignmentsPage";

export function AssignmentPage() {
  const aid = Number(useParams().aid);
  const assignment = useStudentAssignment(aid);
  return (
    <QueryView query={assignment}>
      {(a) => (
        <div className="space-y-6">
          <div>
            <Link to="/student" className="link text-sm">← Assignments</Link>
            <h1 className="text-xl font-semibold">{a.title}</h1>
            <p className="text-sm text-slate-600">
              {a.class_name} · Due <DueDate dueAt={a.due_at} />
            </p>
          </div>
          {a.description_md && (
            <div className="card">
              <Markdown>{a.description_md}</Markdown>
            </div>
          )}
          <div className="card overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Question</th>
                  <th>Difficulty</th>
                  <th>Solved</th>
                </tr>
              </thead>
              <tbody>
                {a.questions.map((q) => (
                  <tr key={q.id}>
                    <td>{q.position}</td>
                    <td>
                      <Link to={`/student/assignments/${a.id}/questions/${q.id}`} className="link">{q.title}</Link>
                    </td>
                    <td>{q.difficulty}</td>
                    <td>{q.solved && <span className="text-green-700" aria-label="solved">✓</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </QueryView>
  );
}
