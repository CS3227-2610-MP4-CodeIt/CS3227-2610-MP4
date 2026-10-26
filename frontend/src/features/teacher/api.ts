import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiFetch } from "../../api/client";
import { keys, prefixes } from "../../api/keys";
import type {
  Assignment,
  AssignmentCreate,
  AssignmentUpdate,
  ClassOut,
  Question,
  QuestionIn,
  QuestionSummary,
} from "../../api/types";

// Teacher queries and mutations; cache updates follow frontend-teacher §1.3.

export const useTeacherClasses = () =>
  useQuery({
    queryKey: keys.teacherClasses(),
    queryFn: ({ signal }) => apiFetch<ClassOut[]>("/teacher/classes", { signal }),
  });

export const useQuestions = () =>
  useQuery({
    queryKey: keys.teacherQuestions(),
    queryFn: ({ signal }) => apiFetch<QuestionSummary[]>("/teacher/questions", { signal }),
  });

export const useQuestion = (id: number) =>
  useQuery({
    queryKey: keys.teacherQuestion(id),
    queryFn: ({ signal }) => apiFetch<Question>(`/teacher/questions/${id}`, { signal }),
  });

export const useAssignments = (classId?: number) =>
  useQuery({
    queryKey: keys.teacherAssignments(classId),
    queryFn: ({ signal }) =>
      apiFetch<Assignment[]>(classId ? `/teacher/assignments?class_id=${classId}` : "/teacher/assignments", {
        signal,
      }),
  });

export const useAssignment = (id: number) =>
  useQuery({
    queryKey: keys.teacherAssignment(id),
    queryFn: ({ signal }) => apiFetch<Assignment>(`/teacher/assignments/${id}`, { signal }),
  });

/** Read-only question of an assignment; works for co-teachers who did not write it. */
export const useAssignmentQuestion = (aid: number, qid: number) =>
  useQuery({
    queryKey: keys.teacherAssignmentQuestion(aid, qid),
    queryFn: ({ signal }) => apiFetch<Question>(`/teacher/assignments/${aid}/questions/${qid}`, { signal }),
  });

/** Store a question returned by create / approve and refresh the list. */
function useQuestionSaved() {
  const qc = useQueryClient();
  return (q: Question) => {
    qc.setQueryData(keys.teacherQuestion(q.id), q);
    void qc.invalidateQueries({ queryKey: keys.teacherQuestions() });
  };
}

export function useCreateQuestion() {
  const onSuccess = useQuestionSaved();
  return useMutation({
    mutationFn: (body: QuestionIn) => apiFetch<Question>("/teacher/questions", { method: "POST", body }),
    onSuccess,
  });
}

export function useUpdateQuestion(id: number) {
  const qc = useQueryClient();
  const saved = useQuestionSaved();
  return useMutation({
    mutationFn: (body: QuestionIn) => apiFetch<Question>(`/teacher/questions/${id}`, { method: "PUT", body }),
    onSuccess: (q) => {
      saved(q);
      // Assignment views show question titles and difficulty.
      void qc.invalidateQueries({ queryKey: prefixes.teacherAssignment });
    },
  });
}

export function useDeleteQuestion(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<void>(`/teacher/questions/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.removeQueries({ queryKey: keys.teacherQuestion(id) });
      void qc.invalidateQueries({ queryKey: keys.teacherQuestions() });
    },
  });
}

export function useApproveDraft() {
  const qc = useQueryClient();
  const onSuccess = useQuestionSaved();
  return useMutation({
    mutationFn: (jobId: number) =>
      apiFetch<Question>(`/teacher/question-generations/${jobId}/approve`, { method: "POST" }),
    onSuccess,
    // 409: approved elsewhere (e.g. another tab) → refetch so the derived "approved" state updates.
    onError: (err) => {
      if (err instanceof ApiError && err.status === 409) void qc.invalidateQueries({ queryKey: keys.teacherQuestions() });
    },
  });
}

function useAssignmentSaved() {
  const qc = useQueryClient();
  return (a: Assignment) => {
    qc.setQueryData(keys.teacherAssignment(a.id), a);
    void qc.invalidateQueries({ queryKey: prefixes.teacherAssignments });
  };
}

export function useCreateAssignment() {
  const onSuccess = useAssignmentSaved();
  return useMutation({
    mutationFn: (body: AssignmentCreate) => apiFetch<Assignment>("/teacher/assignments", { method: "POST", body }),
    onSuccess,
  });
}

export function useUpdateAssignment(id: number) {
  const onSuccess = useAssignmentSaved();
  return useMutation({
    mutationFn: (body: AssignmentUpdate) =>
      apiFetch<Assignment>(`/teacher/assignments/${id}`, { method: "PATCH", body }),
    onSuccess,
  });
}

export function useDeleteAssignment(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<void>(`/teacher/assignments/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.removeQueries({ queryKey: keys.teacherAssignment(id) });
      void qc.invalidateQueries({ queryKey: prefixes.teacherAssignments });
    },
  });
}
