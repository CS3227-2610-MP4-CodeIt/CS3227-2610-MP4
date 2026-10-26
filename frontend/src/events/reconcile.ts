import type { EventSourceMessage } from "@microsoft/fetch-event-source";
import type { QueryClient, QueryKey } from "@tanstack/react-query";
import { keys } from "../api/keys";
import { parseQuestionKey } from "../jobs/endpoints";
import { isJobKind, type JobKind } from "../jobs/types";

export type ServerEvent =
  | { type: "ready" }
  | { type: "job"; job_id: number; kind: string; target_key: string };

// Effect prefixes refetched on `ready` (frontend-spec §4.2).
export const ALL_JOB_EFFECT_PREFIXES: QueryKey[] = [
  ["student", "submissions"],
  ["student", "question"],
  ["student", "assignment"],
  ["student", "assignments"],
];

/** Other data a job changes, invalidated together with the job. */
function jobEffects(kind: JobKind, targetKey: string): QueryKey[] {
  if (kind !== "submit") return [];
  const q = parseQuestionKey(targetKey);
  if (!q) return [];
  return [
    keys.studentSubmissions(q.aid, q.qid),
    keys.studentQuestion(q.aid, q.qid),
    keys.studentAssignment(q.aid),
    keys.studentAssignments(),
  ];
}

export function keysToInvalidate(ev: ServerEvent): QueryKey[] {
  if (ev.type === "ready") return [["jobCheck"], ["job"], ...ALL_JOB_EFFECT_PREFIXES];
  if (!isJobKind(ev.kind)) return [];
  return [keys.jobCheck(ev.kind, ev.target_key), keys.job(ev.job_id), ...jobEffects(ev.kind, ev.target_key)];
}

/** Bad JSON or an unknown event → null (ignored). */
export function parseEvent(msg: Pick<EventSourceMessage, "event" | "data">): ServerEvent | null {
  if (msg.event === "ready") return { type: "ready" };
  if (msg.event !== "job") return null;
  try {
    const d = JSON.parse(msg.data);
    if (typeof d?.job_id === "number" && typeof d.kind === "string" && typeof d.target_key === "string") {
      return { type: "job", job_id: d.job_id, kind: d.kind, target_key: d.target_key };
    }
  } catch {
    // ignore
  }
  return null;
}

export function handleEvent(queryClient: QueryClient, msg: Pick<EventSourceMessage, "event" | "data">) {
  const ev = parseEvent(msg);
  if (!ev) return;
  for (const queryKey of keysToInvalidate(ev)) void queryClient.invalidateQueries({ queryKey });
}
