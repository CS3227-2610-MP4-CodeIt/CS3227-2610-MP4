import { ApiError } from "../../api/client";
import type { Difficulty, Question, QuestionIn } from "../../api/types";

// Question form state and checks (frontend-teacher §1.1), free of React so they can be unit-tested.

export interface TestCaseRow {
  /** Local key so rows keep their identity when moved. */
  key: number;
  stdin: string;
  expected_stdout: string;
  is_hidden: boolean;
}

export interface QuestionForm {
  title: string;
  statement_md: string;
  difficulty: Difficulty;
  topics: string;
  time_limit_ms: string;
  memory_limit_mb: string;
  tolerance: boolean;
  tol_abs: string;
  tol_rel: string;
  test_cases: TestCaseRow[];
}

export const DIFFICULTIES: Difficulty[] = ["easy", "medium", "hard"];

let nextKey = 1;
export const newRow = (is_hidden = false): TestCaseRow => ({ key: nextKey++, stdin: "", expected_stdout: "", is_hidden });

export const emptyForm = (): QuestionForm => ({
  title: "",
  statement_md: "",
  difficulty: "easy",
  topics: "",
  time_limit_ms: "2000",
  memory_limit_mb: "256",
  tolerance: false,
  tol_abs: "0",
  tol_rel: "0",
  test_cases: [newRow(false), newRow(true)],
});

export const formFromQuestion = (q: Question): QuestionForm => ({
  title: q.title,
  statement_md: q.statement_md,
  difficulty: q.difficulty,
  topics: q.topics.join(", "),
  time_limit_ms: String(q.time_limit_ms),
  memory_limit_mb: String(q.memory_limit_mb),
  tolerance: q.float_tolerance !== null,
  tol_abs: String(q.float_tolerance?.abs ?? 0),
  tol_rel: String(q.float_tolerance?.rel ?? 0),
  test_cases: q.test_cases.map((t) => ({ ...newRow(t.is_hidden), stdin: t.stdin, expected_stdout: t.expected_stdout })),
});

/** Comma-separated text → trimmed, lower-cased, de-duplicated topics (as the backend does). */
export function parseTopics(text: string): string[] {
  const out: string[] = [];
  for (const raw of text.split(",")) {
    const t = raw.trim().toLowerCase();
    if (t && !out.includes(t)) out.push(t);
  }
  return out;
}

export function toQuestionIn(f: QuestionForm): QuestionIn {
  return {
    title: f.title,
    statement_md: f.statement_md,
    difficulty: f.difficulty,
    topics: parseTopics(f.topics),
    time_limit_ms: Number(f.time_limit_ms),
    memory_limit_mb: Number(f.memory_limit_mb),
    float_tolerance: f.tolerance ? { abs: Number(f.tol_abs), rel: Number(f.tol_rel) } : null,
    test_cases: f.test_cases.map(({ stdin, expected_stdout, is_hidden }) => ({ stdin, expected_stdout, is_hidden })),
  };
}

const inRange = (value: string, min: number, max: number, int = true) => {
  const n = Number(value);
  return value.trim() !== "" && Number.isFinite(n) && (!int || Number.isInteger(n)) && n >= min && n <= max;
};

/** Client-side checks mirroring the backend; the backend is still the authority. */
export function checkQuestion(f: QuestionForm): string[] {
  const problems: string[] = [];
  if (f.title.trim().length < 1 || f.title.length > 200) problems.push("Title must be 1–200 characters.");
  if (f.statement_md.trim().length < 1 || f.statement_md.length > 20_000) {
    problems.push("Statement must be 1–20 000 characters.");
  }
  const topics = parseTopics(f.topics);
  if (topics.length > 5) problems.push("At most 5 topics.");
  if (topics.some((t) => t.length > 30)) problems.push("Each topic must be at most 30 characters.");
  if (!inRange(f.time_limit_ms, 100, 10_000)) problems.push("Time limit must be 100–10 000 ms.");
  if (!inRange(f.memory_limit_mb, 16, 1024)) problems.push("Memory limit must be 16–1024 MB.");
  if (f.tolerance) {
    if (!inRange(f.tol_abs, 0, 1, false) || !inRange(f.tol_rel, 0, 1, false)) {
      problems.push("Tolerances must be between 0 and 1.");
    } else if (Number(f.tol_abs) === 0 && Number(f.tol_rel) === 0) {
      problems.push("At least one tolerance must be above 0.");
    }
  }
  const n = f.test_cases.length;
  if (n < 2 || n > 50) problems.push("A question needs 2–50 test cases.");
  if (!f.test_cases.some((t) => !t.is_hidden)) problems.push("At least one test case must be visible.");
  if (!f.test_cases.some((t) => t.is_hidden)) problems.push("At least one test case must be hidden.");
  return problems;
}

export interface QuestionErrors {
  /** By top-level field, e.g. `title`, `topics`, `float_tolerance`. */
  fields: Record<string, string>;
  /** By test-case row index (0-based). */
  rows: Record<number, string>;
  /** Everything not tied to a field or row. */
  other: string[];
}

/** Map a 422 list to fields and rows by `loc`, e.g. `["body", "test_cases", 3, "expected_stdout"]` → row 3. */
export function questionErrors(error: unknown): QuestionErrors {
  const out: QuestionErrors = { fields: {}, rows: {}, other: [] };
  if (!(error instanceof ApiError) || error.status !== 422) return out;
  if (typeof error.detail === "string") {
    out.other.push(error.detail);
    return out;
  }
  for (const { loc, msg } of error.detail) {
    const [, field, index, sub] = loc;
    if (field === "test_cases" && typeof index === "number") {
      const text = typeof sub === "string" ? `${sub}: ${msg}` : msg;
      out.rows[index] = out.rows[index] ? `${out.rows[index]}; ${text}` : text;
    } else if (typeof field === "string" && field !== "test_cases") {
      out.fields[field] ??= msg;
    } else {
      out.other.push(msg);
    }
  }
  return out;
}

/** Swap row `i` with row `i + dir`; out-of-range moves are no-ops. */
export function moveItem<T>(items: T[], i: number, dir: -1 | 1): T[] {
  const j = i + dir;
  if (j < 0 || j >= items.length) return items;
  const next = [...items];
  [next[i], next[j]] = [next[j], next[i]];
  return next;
}
