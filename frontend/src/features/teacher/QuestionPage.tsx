import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { ApiError } from "../../api/client";
import type { Difficulty, Question } from "../../api/types";
import { ConfirmButton } from "../../components/ConfirmButton";
import { ErrorText } from "../../components/ErrorText";
import { QueryView } from "../../components/QueryView";
import { useCreateQuestion, useDeleteQuestion, useQuestion, useUpdateQuestion } from "./api";
import { MarkdownField } from "./MarkdownField";
import {
  checkQuestion,
  DIFFICULTIES,
  emptyForm,
  formFromQuestion,
  moveItem,
  newRow,
  parseTopics,
  questionErrors,
  toQuestionIn,
  type QuestionForm,
  type TestCaseRow,
} from "./questionForm";

export function NewQuestionPage() {
  const navigate = useNavigate();
  const create = useCreateQuestion();
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/teacher/questions" className="link text-sm">← Questions</Link>
        <h1 className="text-xl font-semibold">New question</h1>
      </div>
      <QuestionEditor
        initial={emptyForm()}
        error={create.error}
        pending={create.isPending}
        submitLabel="Create question"
        onSave={(body) =>
          create.mutate(body, { onSuccess: (q) => navigate(`/teacher/questions/${q.id}`, { replace: true }) })
        }
      />
    </div>
  );
}

export function QuestionPage() {
  const id = Number(useParams().id);
  const question = useQuestion(id);
  return (
    <QueryView query={question}>
      {(q) => <QuestionDetail key={`${q.id}:${q.updated_at}`} question={q} />}
    </QueryView>
  );
}

function QuestionDetail({ question }: { question: Question }) {
  const navigate = useNavigate();
  const update = useUpdateQuestion(question.id);
  const remove = useDeleteQuestion(question.id);
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-4">
        <Link to="/teacher/questions" className="link text-sm">← Questions</Link>
        <h1 className="text-xl font-semibold">{question.title}</h1>
        {question.source_job_id !== null && (
          <span className="rounded bg-violet-100 px-1.5 py-0.5 text-xs text-violet-700">AI</span>
        )}
      </div>
      {update.isSuccess && <p className="text-sm text-green-700">Saved.</p>}
      <QuestionEditor
        initial={formFromQuestion(question)}
        error={update.error}
        pending={update.isPending}
        submitLabel="Save"
        onSave={(body) => update.mutate(body)}
      />
      <div className="card space-y-2">
        <h2 className="font-medium">Delete question</h2>
        <p className="text-sm text-slate-600">Not possible while an assignment uses it.</p>
        <ConfirmButton
          message={`Delete question "${question.title}"?`}
          disabled={remove.isPending}
          onConfirm={() => remove.mutate(undefined, { onSuccess: () => navigate("/teacher/questions") })}
        >
          Delete
        </ConfirmButton>
        <ErrorText error={remove.error} />
      </div>
    </div>
  );
}

/** Question form (frontend-teacher §1.1). Seeded once from `initial`; the parent remounts it after a save. */
function QuestionEditor({
  initial,
  error,
  pending,
  submitLabel,
  onSave,
}: {
  initial: QuestionForm;
  error: unknown;
  pending: boolean;
  submitLabel: string;
  onSave: (body: ReturnType<typeof toQuestionIn>) => void;
}) {
  const [form, setForm] = useState(initial);
  const set = <K extends keyof QuestionForm>(field: K, value: QuestionForm[K]) =>
    setForm((f) => ({ ...f, [field]: value }));
  const setRows = (fn: (rows: TestCaseRow[]) => TestCaseRow[]) =>
    setForm((f) => ({ ...f, test_cases: fn(f.test_cases) }));

  const problems = checkQuestion(form);
  const server = questionErrors(error);
  const fieldError = (field: string) =>
    server.fields[field] ? <p className="mt-1 text-xs text-red-600">{server.fields[field]}</p> : null;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (problems.length === 0) onSave(toQuestionIn(form));
  };

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="card space-y-3">
        <div>
          <label className="label" htmlFor="q-title">Title</label>
          <input id="q-title" className="input" value={form.title} onChange={(e) => set("title", e.target.value)} />
          {fieldError("title")}
        </div>
        <div>
          <label className="label" htmlFor="q-statement">Statement (Markdown)</label>
          <MarkdownField
            id="q-statement"
            value={form.statement_md}
            onChange={(v) => set("statement_md", v)}
            rows={14}
          />
          {fieldError("statement_md")}
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="label" htmlFor="q-difficulty">Difficulty</label>
            <select
              id="q-difficulty"
              className="input"
              value={form.difficulty}
              onChange={(e) => set("difficulty", e.target.value as Difficulty)}
            >
              {DIFFICULTIES.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="q-topics">Topics (comma-separated)</label>
            <input
              id="q-topics"
              className="input"
              value={form.topics}
              onChange={(e) => set("topics", e.target.value)}
              onBlur={() => set("topics", parseTopics(form.topics).join(", "))}
            />
            {fieldError("topics")}
          </div>
          <div>
            <label className="label" htmlFor="q-time">Time limit (ms)</label>
            <input
              id="q-time"
              type="number"
              className="input"
              value={form.time_limit_ms}
              onChange={(e) => set("time_limit_ms", e.target.value)}
            />
            {fieldError("time_limit_ms")}
          </div>
          <div>
            <label className="label" htmlFor="q-memory">Memory limit (MB)</label>
            <input
              id="q-memory"
              type="number"
              className="input"
              value={form.memory_limit_mb}
              onChange={(e) => set("memory_limit_mb", e.target.value)}
            />
            {fieldError("memory_limit_mb")}
          </div>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.tolerance} onChange={(e) => set("tolerance", e.target.checked)} />
            Compare floats with a tolerance
          </label>
          {form.tolerance && (
            <>
              <div>
                <label className="label" htmlFor="q-abs">Absolute</label>
                <input
                  id="q-abs"
                  type="number"
                  step="any"
                  className="input w-32"
                  value={form.tol_abs}
                  onChange={(e) => set("tol_abs", e.target.value)}
                />
              </div>
              <div>
                <label className="label" htmlFor="q-rel">Relative</label>
                <input
                  id="q-rel"
                  type="number"
                  step="any"
                  className="input w-32"
                  value={form.tol_rel}
                  onChange={(e) => set("tol_rel", e.target.value)}
                />
              </div>
            </>
          )}
        </div>
        {fieldError("float_tolerance")}
      </div>

      <div className="card space-y-3">
        <div className="flex items-center gap-3">
          <h2 className="font-medium">
            Test cases <span className="text-slate-400">({form.test_cases.length})</span>
          </h2>
          <button
            type="button"
            className="btn ml-auto"
            disabled={form.test_cases.length >= 50}
            onClick={() => setRows((rows) => [...rows, newRow(true)])}
          >
            Add test case
          </button>
        </div>
        {form.test_cases.map((row, i) => (
          <TestCaseEditor
            key={row.key}
            row={row}
            index={i}
            count={form.test_cases.length}
            error={server.rows[i]}
            onChange={(next) => setRows((rows) => rows.map((r) => (r.key === row.key ? next : r)))}
            onMove={(dir) => setRows((rows) => moveItem(rows, i, dir))}
            onRemove={() => setRows((rows) => rows.filter((r) => r.key !== row.key))}
          />
        ))}
      </div>

      <div className="space-y-2">
        {problems.length > 0 && (
          <ul className="list-inside list-disc text-sm text-amber-700">
            {problems.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        )}
        {server.other.map((msg) => (
          <p key={msg} className="text-sm text-red-600">{msg}</p>
        ))}
        {/* 422s are shown by their fields above; this covers network errors and anything else. */}
        {!(error instanceof ApiError && error.status === 422) && <ErrorText error={error} />}
        <button type="submit" className="btn btn-primary" disabled={pending || problems.length > 0}>
          {submitLabel}
        </button>
      </div>
    </form>
  );
}

function TestCaseEditor({
  row,
  index,
  count,
  error,
  onChange,
  onMove,
  onRemove,
}: {
  row: TestCaseRow;
  index: number;
  count: number;
  error?: string;
  onChange: (row: TestCaseRow) => void;
  onMove: (dir: -1 | 1) => void;
  onRemove: () => void;
}) {
  return (
    <div className="rounded border border-slate-200 p-3">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-sm">
        <span className="font-medium">#{index + 1}</span>
        <label className="flex items-center gap-1">
          <input
            type="checkbox"
            checked={row.is_hidden}
            onChange={(e) => onChange({ ...row, is_hidden: e.target.checked })}
          />
          Hidden
        </label>
        <div className="ml-auto flex gap-1">
          <button type="button" className="btn px-2 py-0.5" disabled={index === 0} onClick={() => onMove(-1)} aria-label="Move up">↑</button>
          <button type="button" className="btn px-2 py-0.5" disabled={index === count - 1} onClick={() => onMove(1)} aria-label="Move down">↓</button>
          <button type="button" className="btn btn-danger px-2 py-0.5" onClick={onRemove}>Remove</button>
        </div>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        <textarea
          className="input font-mono"
          rows={3}
          placeholder="stdin"
          aria-label={`Test ${index + 1} stdin`}
          value={row.stdin}
          onChange={(e) => onChange({ ...row, stdin: e.target.value })}
        />
        <textarea
          className="input font-mono"
          rows={3}
          placeholder="expected stdout"
          aria-label={`Test ${index + 1} expected stdout`}
          value={row.expected_stdout}
          onChange={(e) => onChange({ ...row, expected_stdout: e.target.value })}
        />
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
