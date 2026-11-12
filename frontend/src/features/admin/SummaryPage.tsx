import { useState } from "react";
import { Link, useParams } from "react-router";
import type { SummaryResult, SummaryStats, Verdict } from "../../api/types";
import { useAuth } from "../../auth/AuthProvider";
import { formatDate } from "../../components/dates";
import { ErrorText } from "../../components/ErrorText";
import { JobStatusBadge } from "../../components/JobStatusBadge";
import { Markdown } from "../../components/Markdown";
import { NotFound } from "../../components/NotFound";
import { QueryView } from "../../components/QueryView";
import { Spinner } from "../../components/Spinner";
import { targetKey } from "../../jobs/endpoints";
import type { Job } from "../../jobs/types";
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
  const { auth } = useAuth();
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
              <Link to={`/admin/classes/${cid}`} className="link text-sm">
                ← {c.name}
              </Link>
              <h1 className="text-xl font-semibold">{assignment.title}</h1>
              <span className="text-sm text-slate-500">
                {assignment.due_at
                  ? `Due ${formatDate(assignment.due_at)}`
                  : "No due date"}
              </span>
            </div>
            {auth && <SummaryPanel key={`${auth.user.id}:${aid}`} aid={aid} />}
          </div>
        );
      }}
    </QueryView>
  );
}

function SummaryPanel({ aid }: { aid: number }) {
  const key = targetKey.assignment(aid);
  const check = useJob<SummaryResult>("assignment_summary", key);
  const start = useStartJob<Record<string, never>, SummaryResult>(
    "assignment_summary",
    key,
  );
  const job = check.data?.job ?? null;
  const running = job?.status === "in_process";
  const [lastSuccess, setLastSuccess] = useState<Job<SummaryResult> | null>(
    null,
  );
  const [regeneratedFrom, setRegeneratedFrom] = useState<number | null>(null);
  // Keep the last observed success in this keyed panel only, independently of
  // the current attempt. A guarded render update avoids an effect's stale frame.
  if (
    job?.status === "success" &&
    job.result &&
    (!lastSuccess || job.id > lastSuccess.id)
  ) {
    setLastSuccess(job);
  }
  const displayed =
    job?.status === "success" &&
    job.result &&
    (!lastSuccess || job.id >= lastSuccess.id)
      ? job
      : lastSuccess;
  // An old request error must not label a later SSE-delivered success as old.
  const requestFailed = start.isError && displayed?.id === regeneratedFrom;
  const previous =
    !!displayed &&
    (start.isPending ||
      requestFailed ||
      check.isError ||
      job?.id !== displayed.id ||
      job?.status !== "success");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          className="btn btn-primary"
          disabled={start.isPending || running || check.isPending}
          onClick={() => {
            setRegeneratedFrom(displayed?.id ?? null);
            start.mutate({});
          }}
        >
          {job ? "Regenerate summary" : "Generate summary"}
        </button>
        {job && <JobStatusBadge job={job} runningLabel="Summarising…" />}
      </div>
      {start.data?.created === false && (
        <p className="text-sm text-slate-600">
          A summary is already being generated.
        </p>
      )}
      <ErrorText error={start.error} />
      {check.isError && (
        <ErrorText error={check.error} onRetry={() => void check.refetch()} />
      )}
      {previous && displayed && (
        <div className="text-sm text-slate-600">
          <p>
            Previous successful result — generated{" "}
            {formatDate(displayed.finished_at ?? displayed.created_at)}.{" "}
            Statistics reflect that generation.
          </p>
          {(job?.status === "failed" || requestFailed) && (
            <p>Regeneration failed. Showing the previous successful result.</p>
          )}
        </div>
      )}
      {displayed?.result ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <StatsTable stats={displayed.result.stats} />
          <div className="card">
            <h2 className="mb-2 font-medium">
              AI summary — check against the numbers
            </h2>
            <Markdown>{displayed.result.summary_md}</Markdown>
          </div>
        </div>
      ) : check.isPending ? (
        <Spinner />
      ) : check.isError ? null : !job ? (
        <p className="text-sm text-slate-500">No summary yet.</p>
      ) : null}
    </div>
  );
}

function StatsTable({ stats }: { stats: SummaryStats }) {
  return (
    <div className="card space-y-3 overflow-x-auto">
      <h2 className="font-medium">Stats</h2>
      <p className="text-sm text-slate-600">
        {stats.students_in_class} students in class ·{" "}
        {stats.students_attempted_any} attempted any ·{" "}
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
              <th key={v.key} title={v.key}>
                {v.label}
              </th>
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
