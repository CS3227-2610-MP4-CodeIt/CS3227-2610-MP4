import type { ReactNode } from "react";
import type { QuestionIn } from "../../api/types";
import { Markdown } from "../../components/Markdown";

/** Read-only question: meta line, statement and all test cases. `testsNote` goes above the table. */
export function QuestionPreview({ question: q, testsNote }: { question: QuestionIn; testsNote?: ReactNode }) {
  return (
    <div className="space-y-4">
      <div className="card space-y-3">
        <h3 className="text-lg font-semibold">{q.title}</h3>
        <p className="text-sm text-slate-600">
          {q.difficulty} · {q.topics.join(", ")} · {q.time_limit_ms} ms · {q.memory_limit_mb} MB
          {q.float_tolerance && ` · tolerance abs ${q.float_tolerance.abs}, rel ${q.float_tolerance.rel}`}
        </p>
        <Markdown>{q.statement_md}</Markdown>
      </div>
      <div className="card space-y-3 overflow-x-auto">
        <h3 className="font-medium">Test cases</h3>
        {testsNote}
        <table className="table">
          <thead>
            <tr>
              <th>#</th>
              <th>stdin</th>
              <th>expected stdout</th>
              <th>Hidden</th>
            </tr>
          </thead>
          <tbody className="align-top">
            {q.test_cases.map((t, i) => (
              <tr key={i}>
                <td>{i + 1}</td>
                <td><pre className="max-h-40 overflow-auto font-mono text-xs whitespace-pre-wrap">{t.stdin}</pre></td>
                <td><pre className="max-h-40 overflow-auto font-mono text-xs whitespace-pre-wrap">{t.expected_stdout}</pre></td>
                <td>{t.is_hidden ? "yes" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
