import type { Verdict } from "../../api/types";

export const VERDICT_LABEL: Record<Verdict, string> = {
  ACCEPTED: "Accepted",
  WRONG_ANSWER: "Wrong answer",
  TIME_LIMIT_EXCEEDED: "Time limit exceeded",
  MEMORY_LIMIT_EXCEEDED: "Memory limit exceeded",
  RUNTIME_ERROR: "Runtime error",
};

/** Text colour per verdict: accepted green, limits amber, the rest red. */
export const VERDICT_CLASS: Record<Verdict, string> = {
  ACCEPTED: "text-green-700",
  WRONG_ANSWER: "text-red-700",
  TIME_LIMIT_EXCEEDED: "text-amber-700",
  MEMORY_LIMIT_EXCEEDED: "text-amber-700",
  RUNTIME_ERROR: "text-red-700",
};

export const isPastDue = (dueAt: string | null, now = Date.now()) => dueAt !== null && new Date(dueAt).getTime() <= now;

export const formatMemory = (kb: number | null) => (kb === null ? "—" : `${(kb / 1024).toFixed(1)} MB`);
