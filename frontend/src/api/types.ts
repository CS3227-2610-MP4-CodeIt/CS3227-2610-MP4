// Mirrors backend/app/schemas.py. Teacher / student types are added with their pages.

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
