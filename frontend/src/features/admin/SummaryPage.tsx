import { Link, useParams } from "react-router";
import type { SummaryResult, SummaryStats, Verdict } from "../../api/types";
import { formatDate } from "../../components/dates";
import { ErrorText } from "../../components/ErrorText";
import { JobStatusBadge } from "../../components/JobStatusBadge";
import { Markdown } from "../../components/Markdown";
import { NotFound } from "../../components/NotFound";
import { QueryView } from "../../components/QueryView";
import { Spinner } from "../../components/Spinner";
import { targetKey } from "../../jobs/endpoints";
import { useJob } from "../../jobs/useJob";
import { useStartJob } from "../../jobs/useStartJob";
import { useClass } from "./api";

const VERDICTS: { key: Verdict; label: string }[] = [
  { key: "ACCEPTED", label: "AC" },
  { key: "WRONG_ANSWER", label: "WA" },
  { key: "TIME_LIMIT_EXCEEDED", label: "TLE" },
  { key: "MEMORY_LIMIT_EXCEEDED", label: "MLE" },
  { key: "RUNTIME_ERROR", label: "RE" },
];

export function SummaryPage() {
  const params = useParams();
  const cid = Number(params.cid);
  const aid = Number(params.aid);
  const cls = useClass(cid);

  return (
    <QueryView query={cls}>
      {(c) => {
        const assignment = c.assignments.find((a) => a.id === aid);
        if (!assignment) return <NotFound />;
        return (
          <div className="space-y-6">
            <div className="flex flex-wrap items-baseline gap-4">
              <Link to={`/admin/classes/${cid}`} className="link text-sm">← {c.name}</Link>
              <h1 className="text-xl font-semibold">{assignment.title}</h1>
              <span className="text-sm text-slate-500">
                {assignment.due_at ? `Due ${formatDate(assignment.due_at)}` : "No due date"}
              </span>
            </div>
            <SummaryPanel aid={aid} />
          </div>
        );
      }}
    </QueryView>
  );
}

function SummaryPanel({ aid }: { aid: number }) {
  const key = targetKey.assignment(aid);
  const check = useJob<SummaryResult>("assignment_summary", key);
  const start = useStartJob<Record<string, never>, SummaryResult>("assignment_summary", key);
  const job = check.data?.job ?? null;
  const running = job?.status === "in_process";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          className="btn btn-primary"
          disabled={start.isPending || running || check.isPending}
          onClick={() => start.mutate({})}
        >
          {job ? "Regenerate summary" : "Generate summary"}
        </button>
        {job && <JobStatusBadge job={job} runningLabel="Summarising…" />}
      </div>
      {start.data?.created === false && (
        <p className="text-sm text-slate-600">A summary is already being generated — showing it.</p>
      )}
      <ErrorText error={start.error} />
      {check.isPending ? (
        <Spinner />
      ) : check.isError ? (
        <ErrorText error={check.error} onRetry={() => void check.refetch()} />
      ) : !job ? (
        <p className="text-sm text-slate-500">No summary yet.</p>
      ) : job.status === "success" && job.result ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <StatsTable stats={job.result.stats} />
          <div className="card">
            <h2 className="mb-2 font-medium">AI summary — check against the numbers</h2>
            <Markdown>{job.result.summary_md}</Markdown>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function StatsTable({ stats }: { stats: SummaryStats }) {
  return (
    <div className="card space-y-3 overflow-x-auto">
      <h2 className="font-medium">Stats</h2>
      <p className="text-sm text-slate-600">
        {stats.students_in_class} students in class · {stats.students_attempted_any} attempted any ·{" "}
        {stats.students_solved_all} solved all
      </p>
      <table className="table">
        <thead>
          <tr>
            <th>#</th>
            <th>Question</th>
            <th>Difficulty</th>
            <th>Attempted</th>
            <th>Correct</th>
            <th>Submissions</th>
            {VERDICTS.map((v) => (
              <th key={v.key} title={v.key}>{v.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {stats.questions.map((q) => (
            <tr key={q.position}>
              <td>{q.position}</td>
              <td>{q.title}</td>
              <td>{q.difficulty}</td>
              <td>{q.attempted}</td>
              <td>{q.correct}</td>
              <td>{q.total_submissions}</td>
              {VERDICTS.map((v) => (
                <td key={v.key}>{q.verdicts[v.key] ?? 0}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
