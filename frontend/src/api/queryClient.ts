import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "./client";

// frontend-spec §3.3: 4xx is never retried; network / 5xx once.
export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: true,
        retry: (n, err) => !(err instanceof ApiError && err.status < 500) && n < 1,
      },
      mutations: { retry: false },
    },
  });
}
