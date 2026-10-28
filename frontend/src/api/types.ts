// Mirrors backend/app/schemas.py.

export type Role = "admin" | "teacher" | "student";
export type MemberRole = "teacher" | "student";
export type Difficulty = "easy" | "medium" | "hard";
export type Verdict =
  | "ACCEPTED"
  | "WRONG_ANSWER"
  | "TIME_LIMIT_EXCEEDED"
  | "MEMORY_LIMIT_EXCEEDED"
  | "RUNTIME_ERROR";

// --- auth ---

export interface User {
  id: number;
  username: string;
  display_name: string;
  role: Role;
}

export interface LoginOut {
  token: string;
  user: User;
}

// --- admin: users ---

export interface UserCreate {
  username: string;
  display_name: string;
  password: string;
  role: MemberRole;
}

export type UserUpdate = Partial<Pick<UserCreate, "username" | "display_name" | "password">>;

export interface ClassBrief {
  id: number;
  name: string;
}

export interface UserDetail extends User {
  classes: ClassBrief[];
}

// --- admin: classes ---

export interface ClassCreate {
  name: string;
  description?: string;
}

export type ClassUpdate = Partial<ClassCreate>;

export interface ClassOut {
  id: number;
  name: string;
  description: string;
  created_at: string;
  teacher_count: number;
  student_count: number;
}

export interface AssignmentBrief {
  id: number;
  title: string;
  due_at: string | null;
  created_at: string;
}

export interface ClassDetail extends ClassOut {
  teachers: User[];
  students: User[];
  assignments: AssignmentBrief[];
}

// --- admin: assignment summary result (backend §7.3) ---

export interface SummaryQuestionStats {
  position: number;
  title: string;
  difficulty: Difficulty;
  attempted: number;
  correct: number;
  total_submissions: number;
  verdicts: Record<Verdict, number>;
}

export interface SummaryStats {
  assignment: { title: string; due_at: string | null; class_name: string };
  students_in_class: number;
  students_attempted_any: number;
  students_solved_all: number;
  questions: SummaryQuestionStats[];
}

export interface SummaryResult {
  stats: SummaryStats;
  summary_md: string;
}

// --- teacher: questions (backend §5.3) ---

export interface FloatTolerance {
  abs: number;
  rel: number;
}

export interface TestCase {
  stdin: string;
  expected_stdout: string;
  is_hidden: boolean;
}

export interface QuestionIn {
  title: string;
  statement_md: string;
  difficulty: Difficulty;
  topics: string[];
  time_limit_ms: number;
  memory_limit_mb: number;
  float_tolerance: FloatTolerance | null;
  test_cases: TestCase[];
}

export interface QuestionSummary {
  id: number;
  title: string;
  difficulty: Difficulty;
  topics: string[];
  time_limit_ms: number;
  memory_limit_mb: number;
  float_tolerance: FloatTolerance | null;
  source_job_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface Question extends QuestionSummary {
  statement_md: string;
  test_cases: (TestCase & { position: number })[];
}

// --- teacher: question generation (backend §7.2) ---

export interface QuestionGenIn {
  difficulty: Difficulty;
  topics: string[];
  prompt: string;
  parent_job_id: number | null;
  feedback: string | null;
}

export interface QuestionDraft extends QuestionIn {
  reference_solution: string;
}

export interface QuestionGenResult {
  draft: QuestionDraft;
}

// --- teacher: assignments ---

export interface AssignmentCreate {
  class_id: number;
  title: string;
  description_md: string;
  due_at: string | null;
  question_ids: number[];
}

export type AssignmentUpdate = Partial<Omit<AssignmentCreate, "class_id">>;

export interface AssignmentQuestion {
  id: number;
  position: number;
  title: string;
  difficulty: Difficulty;
}

export interface Assignment {
  id: number;
  class_id: number;
  class_name: string;
  created_by: number | null;
  title: string;
  description_md: string;
  due_at: string | null;
  created_at: string;
  updated_at: string;
  questions: AssignmentQuestion[];
}

// --- student (backend §5.4) ---

export interface StudentQuestionBrief {
  id: number;
  position: number;
  title: string;
  difficulty: Difficulty;
  solved: boolean;
}

export interface StudentAssignment {
  id: number;
  class_id: number;
  class_name: string;
  title: string;
  description_md: string;
  due_at: string | null;
  questions: StudentQuestionBrief[];
}

export interface VisibleTestCase {
  position: number;
  stdin: string;
  expected_stdout: string;
}

export interface StudentQuestion {
  id: number;
  title: string;
  statement_md: string;
  difficulty: Difficulty;
  topics: string[];
  time_limit_ms: number;
  memory_limit_mb: number;
  float_tolerance: FloatTolerance | null;
  test_cases: VisibleTestCase[];
  solved: boolean;
}

export interface CodeIn {
  code: string;
}

export interface HintIn extends CodeIn {
  question?: string;
}

export interface SubmissionBrief {
  id: number;
  verdict: Verdict;
  passed: number;
  total: number;
  created_at: string;
}

export interface Submission extends SubmissionBrief {
  code: string;
}

// --- student: job results (backend §7.1, §7.4) ---

export interface JudgeTestResult {
  index: number;
  hidden: boolean;
  status: Verdict;
  time_ms: number;
  memory_kb: number | null;
  stdout_preview?: string;
  stderr_preview?: string;
}

export interface JudgeResult {
  verdict: Verdict;
  passed: number;
  total: number;
  failed_test_index: number | null;
  error_message: string | null;
  max_time_ms: number;
  max_memory_kb: number | null;
  results: JudgeTestResult[];
}

export interface HintResult {
  hint_md: string;
  tools_used: string[];
}
