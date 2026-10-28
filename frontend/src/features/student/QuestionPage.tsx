import { python } from "@codemirror/lang-python";
import type { UseQueryResult } from "@tanstack/react-query";
import CodeMirror from "@uiw/react-codemirror";
import { useState, type ReactNode } from "react";
import { Link, useParams } from "react-router";
import type { CodeIn, HintIn, HintResult, JudgeResult, StudentQuestion, Submission } from "../../api/types";
import { useAuth } from "../../auth/AuthProvider";
import { ConfirmButton } from "../../components/ConfirmButton";
import { CopyButton } from "../../components/CopyButton";
import { formatDate } from "../../components/dates";
import { ErrorText } from "../../components/ErrorText";
import { JobStatusBadge } from "../../components/JobStatusBadge";
import { Markdown } from "../../components/Markdown";
import { QueryView } from "../../components/QueryView";
import { Spinner } from "../../components/Spinner";
import { SplitPane } from "../../components/SplitPane";
import { targetKey } from "../../jobs/endpoints";
import type { Job, JobCheckOut } from "../../jobs/types";
import { useJob } from "../../jobs/useJob";
import { useStartJob } from "../../jobs/useStartJob";
import { useStudentAssignment, useStudentQuestion, useSubmission, useSubmissions } from "./api";
import { draftKey, initialCode, loadDraft } from "./drafts";
import { JudgeResultView } from "./JudgeResultView";
import { useDraftSaver } from "./useDraftSaver";
import { isPastDue, VERDICT_CLASS, VERDICT_LABEL } from "./verdict";

type Tab = "run" | "submit" | "hint" | "submissions";

const TABS: { id: Tab; label: string }[] = [
  { id: "run", label: "Run result" },
  { id: "submit", label: "Submit result" },
  { id: "hint", label: "Hint" },
  { id: "submissions", label: "Submissions" },
];

const EXTENSIONS = [python()];

const TOOL_LABEL: Record<string, string> = { get_question: "question", get_code: "your code" };

/** Question page (frontend-student §3). Keyed by ids so editor state never carries over to another question. */
export function QuestionPage() {
  const params = useParams();
  const aid = Number(params.aid);
  const qid = Number(params.qid);
  return <QuestionWorkspace key={`${aid}:${qid}`} aid={aid} qid={qid} />;
}

function QuestionWorkspace({ aid, qid }: { aid: number; qid: number }) {
  const { auth } = useAuth();
  const storageKey = draftKey(auth!.user.id, aid, qid);
  const question = useStudentQuestion(aid, qid);
  const assignment = useStudentAssignment(aid);
  const submissions = useSubmissions(aid, qid);

  // Editor content is local state, set once from draft / latest submission / empty (§1.2, §1.4).
  const [draft] = useState(() => loadDraft(storageKey));
  const [code, setCode] = useState<string | null>(null);
  const latestId = code === null && draft === null ? (submissions.data?.[0]?.id ?? null) : null;
  const latest = useSubmission(aid, qid, latestId);
  if (code === null) {
    const init = initialCode(
      draft,
      submissions.isPending
        ? { status: "pending" }
        : submissions.isError
          ? { status: "error" }
          : submissions.data.length === 0
            ? { status: "none" }
            : latest.isPending
              ? { status: "pending" }
              : latest.isError
                ? { status: "error" }
                : { status: "loaded", code: latest.data.code },
    );
    if (init !== null) setCode(init);
  }
  const scheduleSave = useDraftSaver(storageKey);
  const edit = (value: string) => {
    setCode(value);
    scheduleSave(value);
  };

  const tk = targetKey.question(aid, qid);
  const run = useJob<JudgeResult>("run", tk);
  const startRun = useStartJob<CodeIn, JudgeResult>("run", tk);
  const submit = useJob<JudgeResult>("submit", tk);
  const startSubmit = useStartJob<CodeIn, JudgeResult>("submit", tk);
  const hint = useJob<HintResult>("hint", tk);
  const startHint = useStartJob<HintIn, HintResult>("hint", tk);
  const [asked, setAsked] = useState("");
  const [tab, setTab] = useState<Tab>("run");

  const running = (q: UseQueryResult<JobCheckOut<unknown>>) => q.data?.job?.status === "in_process";
  const empty = !code?.trim();
  const closed = isPastDue(assignment.data?.due_at ?? null);

  return (
    <QueryView query={question}>
      {(q) => (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-x-4 text-sm">
            <Link to={`/student/assignments/${aid}`} className="link">
              ← {assignment.data?.title ?? "Assignment"}
            </Link>
            {assignment.data?.due_at && (
              <span className="text-slate-600">
                Due {formatDate(assignment.data.due_at)}
                {closed && " (closed)"}
              </span>
            )}
          </div>
          <SplitPane
            label="Resize statement and editor"
            left={<Statement question={q} />}
            right={
            <div className="min-w-0 space-y-4">
              <div className="card space-y-3">
                {code === null ? (
                  <Spinner label="Loading your code…" />
                ) : (
                  // Drag the bottom-right corner to change the height.
                  <div className="h-96 min-h-40 resize-y overflow-hidden rounded border border-slate-200">
                    <CodeMirror
                      value={code}
                      onChange={edit}
                      extensions={EXTENSIONS}
                      height="100%"
                      className="h-full text-sm"
                      aria-label="Code editor"
                    />
                  </div>
                )}
                <input
                  className="input"
                  maxLength={500}
                  value={asked}
                  onChange={(e) => setAsked(e.target.value)}
                  placeholder="What are you stuck on? (optional, sent with Get hint)"
                  aria-label="Question for the hint"
                />
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    className="btn"
                    disabled={empty || startRun.isPending || running(run)}
                    onClick={() => {
                      setTab("run");
                      startRun.mutate({ code: code! });
                    }}
                  >
                    Run
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={empty || closed || startSubmit.isPending || running(submit)}
                    onClick={() => {
                      setTab("submit");
                      startSubmit.mutate({ code: code! });
                    }}
                  >
                    {closed ? "Submissions closed" : "Submit"}
                  </button>
                  <button
                    type="button"
                    className="btn ml-auto"
                    disabled={code === null || startHint.isPending || running(hint)}
                    onClick={() => {
                      setTab("hint");
                      const question = asked.trim();
                      startHint.mutate(question ? { code: code || "\n", question } : { code: code || "\n" });
                    }}
                  >
                    Get hint
                  </button>
                </div>
                <NotSentNotice start={startRun.data} current={run.data} what="A run" />
                <NotSentNotice start={startSubmit.data} current={submit.data} what="A submission" />
                <NotSentNotice start={startHint.data} current={hint.data} what="A hint" />
                <ErrorText error={startRun.error} />
                <ErrorText error={startSubmit.error} />
                <ErrorText error={startHint.error} />
              </div>
              <div className="card space-y-3">
                <div className="flex flex-wrap gap-1 border-b border-slate-200 pb-2" role="tablist">
                  {TABS.map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      role="tab"
                      aria-selected={tab === t.id}
                      onClick={() => setTab(t.id)}
                      className={`rounded px-2 py-1 text-sm ${tab === t.id ? "bg-slate-200 font-medium" : "text-slate-600 hover:bg-slate-100"}`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
                {tab === "run" && (
                  <JobPanel query={run} empty="No run yet. Run checks your code on the visible tests." runningLabel="Running…">
                    {(result, job) => <JudgeResultView result={result} sentAt={job.created_at} visibleTests={q.test_cases} />}
                  </JobPanel>
                )}
                {tab === "submit" && (
                  <JobPanel query={submit} empty="No submission yet. Submit judges your code on all tests." runningLabel="Judging…">
                    {(result, job) => <JudgeResultView result={result} sentAt={job.created_at} visibleTests={q.test_cases} />}
                  </JobPanel>
                )}
                {tab === "hint" && (
                  <JobPanel query={hint} empty="No hint yet." runningLabel="Thinking…">
                    {(result) => <HintView result={result} />}
                  </JobPanel>
                )}
                {tab === "submissions" && (
                  <SubmissionsPanel
                    aid={aid}
                    qid={qid}
                    list={submissions}
                    onLoad={(c) => {
                      edit(c);
                      setTab("run");
                    }}
                  />
                )}
              </div>
            </div>
            }
          />
        </div>
      )}
    </QueryView>
  );
}

function Statement({ question: q }: { question: StudentQuestion }) {
  return (
    <div className="min-w-0 space-y-4">
      <div className="card space-y-3">
        <h1 className="text-xl font-semibold">
          {q.title}
          {q.solved && <span className="ml-2 text-base text-green-700">✓ solved</span>}
        </h1>
        <p className="text-sm text-slate-600">
          {q.difficulty} · {q.time_limit_ms} ms · {q.memory_limit_mb} MB
          {q.float_tolerance && ` · tolerance abs ${q.float_tolerance.abs}, rel ${q.float_tolerance.rel}`}
        </p>
        <Markdown>{q.statement_md}</Markdown>
      </div>
      <div className="card space-y-3">
        <h2 className="font-medium">Sample tests</h2>
        {q.test_cases.map((t, i) => (
          <div key={t.position} className="space-y-2">
            <p className="text-sm font-medium">Test {i + 1}</p>
            <div className="grid gap-2 sm:grid-cols-2">
              <Sample label="Input" text={t.stdin} />
              <Sample label="Expected output" text={t.expected_stdout} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Sample({ label, text }: { label: string; text: string }) {
  return (
    <div className="min-w-0">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500">{label}</span>
        <CopyButton text={text} />
      </div>
      <pre className="max-h-48 overflow-auto rounded bg-slate-100 p-2 font-mono text-xs whitespace-pre-wrap">{text}</pre>
    </div>
  );
}

/** "created: false": the backend showed a job already running and ignored the code (frontend-spec §4.5). */
function NotSentNotice({
  start,
  current,
  what,
}: {
  start: { created: boolean; job: Job<unknown> } | undefined;
  current: JobCheckOut<unknown> | undefined;
  what: string;
}) {
  if (start?.created !== false || current?.job?.id !== start.job.id || current.job.status !== "in_process") return null;
  return (
    <p className="text-sm text-slate-600">{what} is already in progress — showing it. Your latest code was not sent.</p>
  );
}

/** Empty / running / failed / result states of one job check (frontend-spec §4.7). */
function JobPanel<R>({
  query,
  empty,
  runningLabel,
  children,
}: {
  query: UseQueryResult<JobCheckOut<R>>;
  empty: string;
  runningLabel: string;
  children: (result: R, job: Job<R>) => ReactNode;
}) {
  if (query.isPending) return <Spinner />;
  if (query.isError) return <ErrorText error={query.error} onRetry={() => void query.refetch()} />;
  const job = query.data.job;
  if (!job) return <p className="text-sm text-slate-500">{empty}</p>;
  return (
    <div className="space-y-3">
      <JobStatusBadge job={job} runningLabel={runningLabel} />
      {job.status === "success" && job.result && children(job.result, job)}
    </div>
  );
}

function HintView({ result }: { result: HintResult }) {
  const looked = result.tools_used.map((t) => TOOL_LABEL[t] ?? t);
  return (
    <div className="space-y-2">
      <Markdown>{result.hint_md}</Markdown>
      {looked.length > 0 && <p className="text-xs text-slate-500">Looked at: {looked.join(", ")}</p>}
    </div>
  );
}

function SubmissionsPanel({
  aid,
  qid,
  list,
  onLoad,
}: {
  aid: number;
  qid: number;
  list: ReturnType<typeof useSubmissions>;
  onLoad: (code: string) => void;
}) {
  const [selected, setSelected] = useState<number | null>(null);
  if (list.isPending) return <Spinner />;
  if (list.isError) return <ErrorText error={list.error} onRetry={() => void list.refetch()} />;
  if (list.data.length === 0) return <p className="text-sm text-slate-500">No submissions yet.</p>;
  return (
    <div className="space-y-3">
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Verdict</th>
              <th>Passed</th>
            </tr>
          </thead>
          <tbody>
            {list.data.map((s) => (
              <tr
                key={s.id}
                onClick={() => setSelected(s.id === selected ? null : s.id)}
                className={`cursor-pointer ${s.id === selected ? "bg-slate-100" : "hover:bg-slate-50"}`}
              >
                <td>
                  <button type="button" className="link" aria-expanded={s.id === selected}>
                    {formatDate(s.created_at)}
                  </button>
                </td>
                <td className={VERDICT_CLASS[s.verdict]}>{VERDICT_LABEL[s.verdict]}</td>
                <td>{s.passed} / {s.total}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selected !== null && <SubmissionCode aid={aid} qid={qid} sid={selected} onLoad={onLoad} />}
    </div>
  );
}

function SubmissionCode({
  aid,
  qid,
  sid,
  onLoad,
}: {
  aid: number;
  qid: number;
  sid: number;
  onLoad: (code: string) => void;
}) {
  const sub = useSubmission(aid, qid, sid);
  if (sub.isPending) return <Spinner />;
  if (sub.isError) return <ErrorText error={sub.error} onRetry={() => void sub.refetch()} />;
  const s: Submission = sub.data;
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">Submitted {formatDate(s.created_at)}</span>
        <ConfirmButton
          className="btn ml-auto"
          message="Replace the editor contents with this submission? Your current draft will be overwritten."
          onConfirm={() => onLoad(s.code)}
        >
          Load into editor
        </ConfirmButton>
      </div>
      <pre className="max-h-96 overflow-auto rounded bg-slate-900 p-3 font-mono text-xs text-slate-100">{s.code}</pre>
    </div>
  );
}
