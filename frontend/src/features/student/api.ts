import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../../api/client";
import { keys } from "../../api/keys";
import type { StudentAssignment, StudentQuestion, Submission, SubmissionBrief } from "../../api/types";

// Student queries. Writes are jobs (run / submit / hint), handled by jobs/ and events/.

const questionPath = (aid: number, qid: number) => `/student/assignments/${aid}/questions/${qid}`;

export const useStudentAssignments = () =>
  useQuery({
    queryKey: keys.studentAssignments(),
    queryFn: ({ signal }) => apiFetch<StudentAssignment[]>("/student/assignments", { signal }),
  });

export const useStudentAssignment = (aid: number) =>
  useQuery({
    queryKey: keys.studentAssignment(aid),
    queryFn: ({ signal }) => apiFetch<StudentAssignment>(`/student/assignments/${aid}`, { signal }),
  });

export const useStudentQuestion = (aid: number, qid: number) =>
  useQuery({
    queryKey: keys.studentQuestion(aid, qid),
    queryFn: ({ signal }) => apiFetch<StudentQuestion>(questionPath(aid, qid), { signal }),
  });

/** Own submissions, newest first (no code bodies). */
export const useSubmissions = (aid: number, qid: number) =>
  useQuery({
    queryKey: keys.studentSubmissions(aid, qid),
    queryFn: ({ signal }) => apiFetch<SubmissionBrief[]>(`${questionPath(aid, qid)}/submissions`, { signal }),
  });

/** One submission with its code. Submissions never change, so it is never stale. */
export const useSubmission = (aid: number, qid: number, sid: number | null) =>
  useQuery({
    queryKey: keys.studentSubmission(aid, qid, sid ?? 0),
    queryFn: ({ signal }) => apiFetch<Submission>(`${questionPath(aid, qid)}/submissions/${sid}`, { signal }),
    enabled: sid !== null,
    staleTime: Infinity,
  });
