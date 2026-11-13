import { useEffect, useState } from "react";
import type { Job } from "../jobs/types";
import { formatElapsed, formatRelative } from "./dates";
import { Spinner } from "./Spinner";

function useNow(active: boolean) {
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [active]);
  return now;
}

/** Status line of a job (frontend-spec §4.7). The feature panel renders the result itself. */
export function JobStatusBadge({
  job,
  runningLabel = "Running…",
}: {
  job: Job<unknown>;
  runningLabel?: string;
}) {
  const now = useNow(job.status === "in_process");
  if (job.status === "in_process") {
    return (
      <span>
        <span role="status" className="sr-only">
          {runningLabel}
        </span>
        <span aria-hidden="true">
          <Spinner
            label={`${runningLabel} ${formatElapsed(job.created_at, now)}`}
          />
        </span>
      </span>
    );
  }
  if (job.status === "failed") {
    return (
      <p role="status" className="text-sm text-red-700">
        {job.error ?? "Failed."}
      </p>
    );
  }
  return (
    <p role="status" className="text-xs text-slate-600">
      finished {formatRelative(job.finished_at ?? job.created_at, now)}
    </p>
  );
}
