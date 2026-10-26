import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import type { Difficulty, QuestionDraft, QuestionGenIn, QuestionGenResult } from "../../api/types";
import { useAuth } from "../../auth/AuthProvider";
import { formatDate } from "../../components/dates";
import { ErrorText } from "../../components/ErrorText";
import { JobStatusBadge } from "../../components/JobStatusBadge";
import { Spinner } from "../../components/Spinner";
import { targetKey } from "../../jobs/endpoints";
import type { Job } from "../../jobs/types";
import { useJob } from "../../jobs/useJob";
import { useJobById } from "../../jobs/useJobById";
import { useStartJob } from "../../jobs/useStartJob";
import { useApproveDraft, useQuestions } from "./api";
import { loadHistory, saveHistory, started, withJob, type DraftHistory } from "./draftHistory";
import { DIFFICULTIES, parseTopics } from "./questionForm";
import { QuestionPreview } from "./QuestionPreview";

type GenJob = Job<QuestionGenResult>;

/** AI question generation (frontend-teacher §2). */
export function GeneratePage() {
  const { auth } = useAuth();
  const userId = auth!.user.id;
  const latestQuery = useJob<QuestionGenResult>("question_gen", targetKey.none);
  const generate = useStartJob<QuestionGenIn, QuestionGenResult>("question_gen", targetKey.none);
  const revise = useStartJob<QuestionGenIn, QuestionGenResult>("question_gen", targetKey.none);
  const latest = latestQuery.data?.job ?? null;

  const [stored, setStored] = useState<DraftHistory>(() => loadHistory(userId));
  // The latest job joins the history as soon as it is seen (also one started in another tab).
  const history = withJob(stored, latest?.id);
  useEffect(() => saveHistory(userId, history), [userId, history]);

  const running = latest?.status === "in_process";
  const busy = running || generate.isPending || revise.isPending;
  const selectedId = history.selectedId ?? latest?.id ?? null;

  const [difficulty, setDifficulty] = useState<Difficulty>("easy");
  const [topics, setTopics] = useState("");
  const [prompt, setPrompt] = useState(history.prompt);
  const topicList = parseTopics(topics);
  const requestOk =
    topicList.length >= 1 && topicList.length <= 5 && topicList.every((t) => t.length <= 30) &&
    prompt.trim().length >= 1 && prompt.length <= 2000;

  const onGenerate = (e: FormEvent) => {
    e.preventDefault();
    const body = { difficulty, topics: topicList, prompt, parent_job_id: null, feedback: null };
    generate.mutate(body, { onSuccess: (res) => setStored((h) => started(withJob(h, latest?.id), res.job.id, prompt)) });
  };

  const onRevise = (draftJob: GenJob, feedback: string, onDone: () => void) => {
    const draft = draftJob.result!.draft;
    const revisePrompt = history.prompt || prompt;
    const body = {
      difficulty: draft.difficulty,
      topics: draft.topics,
      prompt: revisePrompt,
      parent_job_id: draftJob.id,
      feedback,
    };
    revise.mutate(body, {
      onSuccess: (res) => {
        setStored((h) => started(withJob(h, latest?.id), res.job.id, revisePrompt));
        onDone();
      },
    });
  };

  const notCreated = generate.data?.created === false || revise.data?.created === false;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/teacher/questions" className="link text-sm">← Questions</Link>
        <h1 className="text-xl font-semibold">Generate a question with AI</h1>
      </div>
      <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
        <div className="space-y-6">
          <form onSubmit={onGenerate} className="card space-y-3">
            <h2 className="font-medium">Request</h2>
            <div>
              <label className="label" htmlFor="gen-difficulty">Difficulty</label>
              <select
                id="gen-difficulty"
                className="input"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value as Difficulty)}
              >
                {DIFFICULTIES.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label" htmlFor="gen-topics">Topics (1–5, comma-separated)</label>
              <input
                id="gen-topics"
                className="input"
                value={topics}
                onChange={(e) => setTopics(e.target.value)}
                onBlur={() => setTopics(topicList.join(", "))}
              />
            </div>
            <div>
              <label className="label" htmlFor="gen-prompt">Prompt</label>
              <textarea
                id="gen-prompt"
                className="input"
                rows={5}
                maxLength={2000}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g. Shortest path in a grid with walls, story about a delivery robot"
              />
            </div>
            <ErrorText error={generate.error} />
            <button type="submit" className="btn btn-primary" disabled={busy || !requestOk}>
              Generate
            </button>
            {notCreated && (
              <p className="text-sm text-slate-600">
                A generation is already in progress — showing it. Your request was not sent.
              </p>
            )}
          </form>
          <HistoryList
            ids={history.jobIds}
            selectedId={selectedId}
            onSelect={(id) => setStored((h) => ({ ...withJob(h, latest?.id), selectedId: id }))}
          />
        </div>
        <div>
          {latestQuery.isPending ? (
            <Spinner />
          ) : latestQuery.isError ? (
            <ErrorText error={latestQuery.error} onRetry={() => void latestQuery.refetch()} />
          ) : selectedId === null ? (
            <p className="text-sm text-slate-500">No drafts yet. Fill in the request and click Generate.</p>
          ) : (
            <DraftView
              key={selectedId}
              id={selectedId}
              latest={latest}
              canRevise={!busy && !!(history.prompt || prompt.trim())}
              reviseError={revise.error}
              onRevise={onRevise}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function HistoryList({
  ids,
  selectedId,
  onSelect,
}: {
  ids: number[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  if (ids.length === 0) return null;
  return (
    <div className="card space-y-2">
      <h2 className="font-medium">Drafts this session</h2>
      <ul className="space-y-1 text-sm">
        {[...ids].reverse().map((id) => (
          <HistoryItem key={id} id={id} selected={id === selectedId} onSelect={() => onSelect(id)} />
        ))}
      </ul>
    </div>
  );
}

function HistoryItem({ id, selected, onSelect }: { id: number; selected: boolean; onSelect: () => void }) {
  const job = useJobById<QuestionGenResult>(id);
  const label = job.isPending
    ? "Loading…"
    : job.isError
      ? "Unavailable"
      : job.data.status === "in_process"
        ? "Generating…"
        : job.data.status === "failed"
          ? "Failed"
          : (job.data.result?.draft.title ?? "Draft");
  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        className={`w-full rounded px-2 py-1 text-left ${selected ? "bg-slate-200 font-medium" : "hover:bg-slate-100"}`}
      >
        <span className="text-slate-400">#{id}</span> {label}
        {job.data && <span className="block text-xs text-slate-500">{formatDate(job.data.created_at)}</span>}
      </button>
    </li>
  );
}

function DraftView({
  id,
  latest,
  canRevise,
  reviseError,
  onRevise,
}: {
  id: number;
  latest: GenJob | null;
  canRevise: boolean;
  reviseError: unknown;
  onRevise: (job: GenJob, feedback: string, onDone: () => void) => void;
}) {
  const byId = useJobById<QuestionGenResult>(latest?.id === id ? null : id);
  // The latest job comes from the check query, which is filled straight from the POST response.
  const job = latest?.id === id ? latest : byId.data;

  if (!job) {
    if (byId.isError) return <ErrorText error={byId.error} onRetry={() => void byId.refetch()} />;
    return <Spinner />;
  }
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h2 className="font-medium">Draft #{job.id}</h2>
        <JobStatusBadge job={job} runningLabel="Generating… this can take a minute." />
      </div>
      {job.status === "success" && job.result && (
        <>
          <ApproveBox job={job} />
          <DraftDetails draft={job.result.draft} />
          <ReviseBox job={job} canRevise={canRevise} error={reviseError} onRevise={onRevise} />
        </>
      )}
    </div>
  );
}

function ApproveBox({ job }: { job: GenJob }) {
  const navigate = useNavigate();
  const questions = useQuestions();
  const approve = useApproveDraft();
  // Approved state is derived from the question list, never stored (frontend-teacher §2.3).
  const approved = questions.data?.find((q) => q.source_job_id === job.id);

  if (approved) {
    return (
      <div className="card text-sm">
        Approved — <Link to={`/teacher/questions/${approved.id}`} className="link">open question</Link>
      </div>
    );
  }
  return (
    <div className="card flex flex-wrap items-center gap-3">
      <button
        type="button"
        className="btn btn-primary"
        disabled={approve.isPending || questions.isPending}
        onClick={() => approve.mutate(job.id, { onSuccess: (q) => navigate(`/teacher/questions/${q.id}`) })}
      >
        Approve
      </button>
      <span className="text-sm text-slate-600">Creates a question you can then edit.</span>
      <ErrorText error={approve.error} messages={{ 409: "This draft was already approved." }} />
    </div>
  );
}

function DraftDetails({ draft }: { draft: QuestionDraft }) {
  const [copied, setCopied] = useState(false);
  const copy = () =>
    void navigator.clipboard.writeText(draft.reference_solution).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });

  return (
    <div className="space-y-4">
      <QuestionPreview
        question={draft}
        testsNote={
          <p className="text-sm text-amber-700">
            Expected outputs are written by the AI and may be wrong. Check them against the reference solution.
          </p>
        }
      />
      <div className="card space-y-2">
        <div className="flex items-center gap-3">
          <h3 className="font-medium">Reference solution</h3>
          <button type="button" className="btn ml-auto px-2 py-0.5 text-xs" onClick={copy}>
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
        <pre className="max-h-96 overflow-auto rounded bg-slate-900 p-3 font-mono text-xs text-slate-100">
          {draft.reference_solution}
        </pre>
      </div>
    </div>
  );
}

function ReviseBox({
  job,
  canRevise,
  error,
  onRevise,
}: {
  job: GenJob;
  canRevise: boolean;
  error: unknown;
  onRevise: (job: GenJob, feedback: string, onDone: () => void) => void;
}) {
  const [feedback, setFeedback] = useState("");
  const ok = feedback.trim().length >= 1 && feedback.length <= 2000;
  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    onRevise(job, feedback, () => setFeedback(""));
  };
  return (
    <form onSubmit={onSubmit} className="card space-y-3">
      <h3 className="font-medium">Revise this draft</h3>
      <textarea
        className="input"
        rows={3}
        maxLength={2000}
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder='e.g. "make n up to 1e5", "add a story"'
        aria-label="Feedback"
      />
      {!canRevise && (
        <p className="text-xs text-slate-500">Fill in the prompt in the request form first, or wait for the running draft.</p>
      )}
      <ErrorText error={error} />
      <button type="submit" className="btn btn-primary" disabled={!canRevise || !ok}>
        Revise
      </button>
    </form>
  );
}
