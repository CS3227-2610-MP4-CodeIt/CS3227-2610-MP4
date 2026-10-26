import type { UseQueryResult } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { ApiError } from "../api/client";
import { ErrorText } from "./ErrorText";
import { NotFound } from "./NotFound";
import { Spinner } from "./Spinner";

/** Loading / 404 / error states for a page's main query. */
export function QueryView<T>({ query, children }: { query: UseQueryResult<T>; children: (data: T) => ReactNode }) {
  if (query.isPending) return <Spinner />;
  if (query.isError) {
    if (query.error instanceof ApiError && query.error.status === 404) return <NotFound />;
    return <ErrorText error={query.error} onRetry={() => void query.refetch()} />;
  }
  return children(query.data);
}
