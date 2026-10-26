import type { JobKind } from "./types";

// The backend's own target keys (backend §6.1).
export const targetKey = {
  question: (aid: number, qid: number) => `a${aid}:q${qid}`,
  assignment: (aid: number) => `a${aid}`,
  none: "-",
} as const;

export function parseQuestionKey(key: string): { aid: number; qid: number } | null {
  const m = /^a(\d+):q(\d+)$/.exec(key);
  return m ? { aid: Number(m[1]), qid: Number(m[2]) } : null;
}

export function parseAssignmentKey(key: string): number | null {
  const m = /^a(\d+)$/.exec(key);
  return m ? Number(m[1]) : null;
}

/** Check (`GET`) and new (`POST`) share one URL per kind (frontend-spec §3.2). */
export function jobUrl(kind: JobKind, key: string): string {
  switch (kind) {
    case "run":
    case "submit":
    case "hint": {
      const q = parseQuestionKey(key);
      if (!q) throw new Error(`bad target key for ${kind}: ${key}`);
      return `/student/assignments/${q.aid}/questions/${q.qid}/${kind}`;
    }
    case "question_gen":
      return "/teacher/question-generations";
    case "assignment_summary": {
      const aid = parseAssignmentKey(key);
      if (aid === null) throw new Error(`bad target key for ${kind}: ${key}`);
      return `/admin/assignments/${aid}/summary`;
    }
  }
}
