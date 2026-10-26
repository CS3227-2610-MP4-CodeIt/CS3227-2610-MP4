import { isFinal, type JobCheckOut } from "./types";

/**
 * Monotonic merge of two writers into one jobCheck entry (frontend-spec §4.4): a higher id wins,
 * and a job never goes from final back to `in_process` or from a job back to "no job".
 */
export function mergeJob<R>(prev: JobCheckOut<R> | undefined, next: JobCheckOut<R>): JobCheckOut<R> {
  const p = prev?.job;
  const n = next.job;
  if (!p) return next;
  if (!n) return prev;
  if (n.id < p.id) return prev;
  if (n.id === p.id && isFinal(p.status) && n.status === "in_process") return prev;
  return next;
}
