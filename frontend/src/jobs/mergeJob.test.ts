import { describe, expect, it } from "vitest";
import { mergeJob } from "./mergeJob";
import type { Job, JobStatus } from "./types";

const job = (id: number, status: JobStatus): Job => ({
  id,
  kind: "run",
  status,
  result: null,
  error: null,
  created_at: "2026-10-21T08:30:00Z",
  finished_at: null,
});

describe("mergeJob", () => {
  it("keeps the newer job when an older id arrives after it", () => {
    const prev = { job: job(43, "in_process") };
    expect(mergeJob(prev, { job: job(42, "success") })).toBe(prev);
  });

  it("keeps success when the same job arrives as in_process", () => {
    const prev = { job: job(43, "success") };
    expect(mergeJob(prev, { job: job(43, "in_process") })).toBe(prev);
  });

  it("keeps the job when null arrives after it", () => {
    const prev = { job: job(42, "failed") };
    expect(mergeJob(prev, { job: null })).toBe(prev);
  });

  it("takes a newer id or a later status of the same job", () => {
    const newer = { job: job(44, "in_process") };
    expect(mergeJob({ job: job(43, "success") }, newer)).toBe(newer);
    const finished = { job: job(43, "success") };
    expect(mergeJob({ job: job(43, "in_process") }, finished)).toBe(finished);
    expect(mergeJob(undefined, newer)).toBe(newer);
  });
});
