import { useState, type FormEvent, type ReactNode } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router";
import type { Assignment, AssignmentUpdate } from "../../api/types";
import { useAuth } from "../../auth/AuthProvider";
import { ConfirmButton } from "../../components/ConfirmButton";
import { formatDate, fromLocalInput, toLocalInput } from "../../components/dates";
import { ErrorText, FieldError } from "../../components/ErrorText";
import { Markdown } from "../../components/Markdown";
import { QueryView } from "../../components/QueryView";
import {
  useAssignment,
  useAssignmentQuestion,
  useCreateAssignment,
  useDeleteAssignment,
  useQuestions,
  useTeacherClasses,
  useUpdateAssignment,
} from "./api";
import { MarkdownField } from "./MarkdownField";
import { QuestionPreview } from "./QuestionPreview";
import { moveItem } from "./questionForm";

const NOT_CREATOR = { 404: "Only the teacher who created this assignment can change it." };
const FIELDS = ["class_id", "title", "description_md", "due_at", "question_ids"];

interface AssignmentFields {
  title: string;
  description: string;
  /** `datetime-local` value, "" for no due date. */
  due: string;
  questionIds: number[];
}

export function NewAssignmentPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const classes = useTeacherClasses();
  const create = useCreateAssignment();
  const [classId, setClassId] = useState(params.get("class_id") ?? "");

  const onSave = (f: AssignmentFields) =>
    create.mutate(
      {
        class_id: Number(classId),
        title: f.title,
        description_md: f.description,
        due_at: fromLocalInput(f.due),
        question_ids: f.questionIds,
      },
      { onSuccess: (a) => navigate(`/teacher/assignments/${a.id}`, { replace: true }) },
    );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/teacher/assignments" className="link text-sm">← Assignments</Link>
        <h1 className="text-xl font-semibold">New assignment</h1>
      </div>
      <AssignmentForm
        initial={{ title: "", description: "", due: "", questionIds: [] }}
        error={create.error}
        pending={create.isPending}
        submitLabel="Create assignment"
        canSave={(f) => classId !== "" && f.questionIds.length > 0}
        onSave={onSave}
      >
        <div>
          <label className="label" htmlFor="a-class">Class</label>
          <select id="a-class" className="input" value={classId} onChange={(e) => setClassId(e.target.value)}>
            <option value="">Choose a class…</option>
            {classes.data?.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          {classes.data?.length === 0 && (
            <p className="mt-1 text-xs text-slate-500">You are not in any class yet. Ask an admin to add you.</p>
          )}
          <ErrorText error={classes.error} onRetry={() => void classes.refetch()} />
          <FieldError error={create.error} field="class_id" />
        </div>
      </AssignmentForm>
    </div>
  );
}

export function AssignmentQuestionPage() {
  const params = useParams();
  const aid = Number(params.id);
  const question = useAssignmentQuestion(aid, Number(params.qid));
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to={`/teacher/assignments/${aid}`} className="link text-sm">← Assignment</Link>
        <span className="text-sm text-slate-500">Read-only</span>
      </div>
      <QueryView query={question}>{(q) => <QuestionPreview question={q} />}</QueryView>
    </div>
  );
}

export function AssignmentPage() {
  const id = Number(useParams().id);
  const assignment = useAssignment(id);
  return <QueryView query={assignment}>{(a) => <AssignmentDetail assignment={a} />}</QueryView>;
}

function AssignmentDetail({ assignment: a }: { assignment: Assignment }) {
  const { auth } = useAuth();
  const navigate = useNavigate();
  const remove = useDeleteAssignment(a.id);
  // Only the creator may edit or delete (backend §3); a deleted creator (null) means nobody can.
  const isCreator = a.created_by !== null && a.created_by === auth?.user.id;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-baseline gap-4">
        <Link to={`/teacher/assignments?class_id=${a.class_id}`} className="link text-sm">← Assignments</Link>
        <h1 className="text-xl font-semibold">{a.title}</h1>
        <span className="text-sm text-slate-500">
          {a.class_name} · {a.due_at ? `due ${formatDate(a.due_at)}` : "no due date"}
        </span>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card space-y-3 self-start">
          <h2 className="font-medium">Questions</h2>
          <ol className="list-inside list-decimal space-y-1 text-sm">
            {a.questions.map((q) => (
              <li key={q.id}>
                {/* Co-teachers cannot open the creator's questions in the editor, only read-only. */}
                <Link
                  to={isCreator ? `/teacher/questions/${q.id}` : `/teacher/assignments/${a.id}/questions/${q.id}`}
                  className="link"
                >
                  {q.title}
                </Link>{" "}
                <span className="text-slate-500">({q.difficulty})</span>
              </li>
            ))}
          </ol>
        </div>
        <div className="card space-y-2 self-start">
          <h2 className="font-medium">Description</h2>
          {a.description_md.trim() ? (
            <Markdown>{a.description_md}</Markdown>
          ) : (
            <p className="text-sm text-slate-500">No description.</p>
          )}
        </div>
      </div>
      {isCreator ? (
        <>
          <EditAssignment key={`${a.id}:${a.updated_at}`} assignment={a} />
          <div className="card space-y-2">
            <h2 className="font-medium">Delete assignment</h2>
            <p className="text-sm text-slate-600">Also deletes all its submissions.</p>
            <ConfirmButton
              message={`Delete assignment "${a.title}" and its submissions?`}
              disabled={remove.isPending}
              onConfirm={() => remove.mutate(undefined, { onSuccess: () => navigate("/teacher/assignments") })}
            >
              Delete
            </ConfirmButton>
            <ErrorText error={remove.error} messages={NOT_CREATOR} />
          </div>
        </>
      ) : (
        <p className="text-sm text-slate-500">Only the teacher who created this assignment can change it.</p>
      )}
    </div>
  );
}

function EditAssignment({ assignment: a }: { assignment: Assignment }) {
  const update = useUpdateAssignment(a.id);
  const initial: AssignmentFields = {
    title: a.title,
    description: a.description_md,
    due: a.due_at ? toLocalInput(a.due_at) : "",
    questionIds: a.questions.map((q) => q.id),
  };

  // Only changed fields are sent; `due_at: null` clears the deadline.
  const changes = (f: AssignmentFields): AssignmentUpdate => {
    const body: AssignmentUpdate = {};
    if (f.title !== initial.title) body.title = f.title;
    if (f.description !== initial.description) body.description_md = f.description;
    if (f.due !== initial.due) body.due_at = fromLocalInput(f.due);
    if (f.questionIds.join() !== initial.questionIds.join()) body.question_ids = f.questionIds;
    return body;
  };

  return (
    <>
      <h2 className="text-lg font-semibold">Edit</h2>
      <AssignmentForm
        initial={initial}
        error={update.error}
        pending={update.isPending}
        submitLabel="Save"
        canSave={(f) => f.questionIds.length > 0 && Object.keys(changes(f)).length > 0}
        onSave={(f) => update.mutate(changes(f))}
        messages={NOT_CREATOR}
      />
    </>
  );
}

/** Assignment form (frontend-teacher §1.2); `children` holds the create-only class picker. */
function AssignmentForm({
  initial,
  error,
  pending,
  submitLabel,
  canSave,
  onSave,
  messages,
  children,
}: {
  initial: AssignmentFields;
  error: unknown;
  pending: boolean;
  submitLabel: string;
  canSave: (f: AssignmentFields) => boolean;
  onSave: (f: AssignmentFields) => void;
  messages?: Record<number, string>;
  children?: ReactNode;
}) {
  const questions = useQuestions();
  const [form, setForm] = useState(initial);
  const [pick, setPick] = useState("");
  const set = <K extends keyof AssignmentFields>(field: K, value: AssignmentFields[K]) =>
    setForm((f) => ({ ...f, [field]: value }));

  const byId = new Map(questions.data?.map((q) => [q.id, q]));
  const available = (questions.data ?? []).filter((q) => !form.questionIds.includes(q.id));
  const titleOk = form.title.trim().length >= 1 && form.title.length <= 200;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <form onSubmit={onSubmit} className="card space-y-3">
      {children}
      <div>
        <label className="label" htmlFor="a-title">Title</label>
        <input id="a-title" className="input" value={form.title} onChange={(e) => set("title", e.target.value)} />
        <FieldError error={error} field="title" />
      </div>
      <div>
        <label className="label" htmlFor="a-desc">Description (Markdown, optional)</label>
        <MarkdownField id="a-desc" value={form.description} onChange={(v) => set("description", v)} rows={6} />
        <FieldError error={error} field="description_md" />
      </div>
      <div>
        <label className="label" htmlFor="a-due">Due date (optional, your local time)</label>
        <div className="flex gap-2">
          <input
            id="a-due"
            type="datetime-local"
            className="input w-auto"
            value={form.due}
            onChange={(e) => set("due", e.target.value)}
          />
          {form.due && (
            <button type="button" className="btn" onClick={() => set("due", "")}>Clear</button>
          )}
        </div>
        <FieldError error={error} field="due_at" />
      </div>
      <div className="space-y-2">
        <span className="label">Questions (1–3, in order)</span>
        {form.questionIds.length === 0 ? (
          <p className="text-sm text-slate-500">No questions picked.</p>
        ) : (
          <ol className="space-y-1 text-sm">
            {form.questionIds.map((qid, i) => (
              <li key={qid} className="flex items-center gap-2 rounded border border-slate-200 px-2 py-1">
                <span className="text-slate-400">{i + 1}.</span>
                {byId.get(qid)?.title ?? `Question #${qid}`}
                <div className="ml-auto flex gap-1">
                  <button
                    type="button"
                    className="btn px-2 py-0.5"
                    disabled={i === 0}
                    onClick={() => set("questionIds", moveItem(form.questionIds, i, -1))}
                    aria-label="Move up"
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    className="btn px-2 py-0.5"
                    disabled={i === form.questionIds.length - 1}
                    onClick={() => set("questionIds", moveItem(form.questionIds, i, 1))}
                    aria-label="Move down"
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    className="btn btn-danger px-2 py-0.5"
                    onClick={() => set("questionIds", form.questionIds.filter((id) => id !== qid))}
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ol>
        )}
        {form.questionIds.length < 3 && (
          <div className="flex gap-2">
            <select className="input" value={pick} onChange={(e) => setPick(e.target.value)} aria-label="Question to add">
              <option value="">{questions.isPending ? "Loading questions…" : "Choose a question…"}</option>
              {available.map((q) => (
                <option key={q.id} value={q.id}>{q.title} ({q.difficulty})</option>
              ))}
            </select>
            <button
              type="button"
              className="btn"
              disabled={!pick}
              onClick={() => {
                set("questionIds", [...form.questionIds, Number(pick)]);
                setPick("");
              }}
            >
              Add
            </button>
          </div>
        )}
        {questions.data?.length === 0 && (
          <p className="text-xs text-slate-500">
            You have no questions yet. <Link to="/teacher/questions/new" className="link">Create one</Link> first.
          </p>
        )}
        <ErrorText error={questions.error} onRetry={() => void questions.refetch()} />
        <FieldError error={error} field="question_ids" />
      </div>
      <ErrorText error={error} fields={FIELDS} messages={messages} />
      <button type="submit" className="btn btn-primary" disabled={pending || !titleOk || !canSave(form)}>
        {submitLabel}
      </button>
    </form>
  );
}
