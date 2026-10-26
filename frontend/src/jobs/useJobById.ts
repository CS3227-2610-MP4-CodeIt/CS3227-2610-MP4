import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../api/client";
import { keys } from "../api/keys";
import { isFinal, type Job } from "./types";

/** One job by id (`GET /jobs/{id}`). Final jobs never change, so they are never stale (frontend-spec §3.3). */
export function useJobById<R>(id: number | null) {
  return useQuery({
    queryKey: keys.job(id ?? 0),
    queryFn: ({ signal }) => apiFetch<Job<R>>(`/jobs/${id}`, { signal }),
    enabled: id !== null,
    staleTime: (query) => (query.state.data && isFinal(query.state.data.status) ? Infinity : 30_000),
  });
}
