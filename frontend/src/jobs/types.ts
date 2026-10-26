export const JOB_KINDS = ["run", "submit", "hint", "question_gen", "assignment_summary"] as const;
export type JobKind = (typeof JOB_KINDS)[number];
export type JobStatus = "in_process" | "success" | "failed";

export interface Job<R = Record<string, unknown>> {
  id: number;
  kind: JobKind;
  status: JobStatus;
  result: R | null;
  error: string | null;
  created_at: string;
  finished_at: string | null;
}

export interface JobCheckOut<R = Record<string, unknown>> {
  job: Job<R> | null;
}

export interface JobNewOut<R = Record<string, unknown>> {
  created: boolean;
  job: Job<R>;
}

export const isJobKind = (kind: unknown): kind is JobKind => JOB_KINDS.includes(kind as JobKind);

export const isFinal = (status: JobStatus) => status === "success" || status === "failed";
