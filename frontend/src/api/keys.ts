import type { JobKind } from "../jobs/types";
import type { Role } from "./types";

// Every query key in the app (frontend-spec §3.2). Pages never write key arrays by hand.
export const keys = {
  me: () => ["me"],
  // admin
  adminUsers: (role?: Role) => ["admin", "users", { role }],
  adminUser: (id: number) => ["admin", "user", id],
  adminClasses: () => ["admin", "classes"],
  adminClass: (id: number) => ["admin", "class", id],
  // teacher
  teacherClasses: () => ["teacher", "classes"],
  teacherQuestions: () => ["teacher", "questions"],
  teacherQuestion: (id: number) => ["teacher", "question", id],
  teacherAssignments: (classId?: number) => ["teacher", "assignments", { classId }],
  teacherAssignment: (id: number) => ["teacher", "assignment", id],
  // student
  studentAssignments: () => ["student", "assignments"],
  studentAssignment: (aid: number) => ["student", "assignment", aid],
  studentQuestion: (aid: number, qid: number) => ["student", "question", aid, qid],
  studentSubmissions: (aid: number, qid: number) => ["student", "submissions", aid, qid],
  studentSubmission: (aid: number, qid: number, sid: number) => ["student", "submission", aid, qid, sid],
  // jobs
  jobCheck: (kind: JobKind, targetKey: string) => ["jobCheck", kind, targetKey],
  job: (id: number) => ["job", id],
} as const;

// Prefixes for invalidating whole groups (every role filter / id).
export const prefixes = {
  adminUsers: ["admin", "users"],
  adminUser: ["admin", "user"],
  adminClass: ["admin", "class"],
} as const;
