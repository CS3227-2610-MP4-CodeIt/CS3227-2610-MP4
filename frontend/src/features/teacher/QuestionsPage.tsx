import { Link } from "react-router";
import { QueryView } from "../../components/QueryView";
import { useQuestions } from "./api";

export function QuestionsPage() {
  const questions = useQuestions();
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">Questions</h1>
        <Link to="/teacher/questions/new" className="btn btn-primary ml-auto">New question</Link>
        <Link to="/teacher/generate" className="btn">Generate with AI</Link>
      </div>
      <div className="card overflow-x-auto">
        <QueryView query={questions}>
          {(list) =>
            list.length === 0 ? (
              <p className="text-sm text-slate-500">No questions yet.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Difficulty</th>
                    <th>Topics</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((q) => (
                    <tr key={q.id}>
                      <td>
                        <Link to={`/teacher/questions/${q.id}`} className="link">{q.title}</Link>
                        {q.source_job_id !== null && (
                          <span className="ml-2 rounded bg-violet-100 px-1.5 py-0.5 text-xs text-violet-700">AI</span>
                        )}
                      </td>
                      <td>{q.difficulty}</td>
                      <td className="text-slate-600">{q.topics.join(", ")}</td>
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
