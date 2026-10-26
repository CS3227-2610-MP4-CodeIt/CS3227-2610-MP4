import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../api/client";
import { keys } from "../api/keys";
import { jobUrl } from "./endpoints";
import { mergeJob } from "./mergeJob";
import type { JobCheckOut, JobKind, JobNewOut } from "./types";

/** "New" request; writes the returned job straight into the check query (frontend-spec §4.5). */
export function useStartJob<Body, R = Record<string, unknown>>(kind: JobKind, targetKey: string) {
  const queryClient = useQueryClient();
  const queryKey = keys.jobCheck(kind, targetKey);
  return useMutation({
    mutationFn: (body: Body) => apiFetch<JobNewOut<R>>(jobUrl(kind, targetKey), { method: "POST", body }),
    onSuccess: async (res) => {
      await queryClient.cancelQueries({ queryKey });
      queryClient.setQueryData<JobCheckOut<R>>(queryKey, (prev) => mergeJob(prev, { job: res.job }));
    },
  });
}
