import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../api/client";
import { keys } from "../api/keys";
import { jobUrl } from "./endpoints";
import { mergeJob } from "./mergeJob";
import type { JobCheckOut, JobKind } from "./types";

/** Read the latest job for (kind, targetKey). Never polls; SSE events refetch it (frontend-spec §4.3). */
export function useJob<R>(kind: JobKind, targetKey: string) {
  const queryClient = useQueryClient();
  const queryKey = keys.jobCheck(kind, targetKey);
  return useQuery({
    queryKey,
    queryFn: async ({ signal }) => {
      const next = await apiFetch<JobCheckOut<R>>(jobUrl(kind, targetKey), { signal });
      return mergeJob(queryClient.getQueryData<JobCheckOut<R>>(queryKey), next);
    },
  });
}
