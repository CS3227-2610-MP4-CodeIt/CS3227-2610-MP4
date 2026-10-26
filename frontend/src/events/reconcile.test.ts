import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import { keys } from "../api/keys";
import { ALL_JOB_EFFECT_PREFIXES, handleEvent, keysToInvalidate, parseEvent } from "./reconcile";

describe("keysToInvalidate", () => {
  it("covers the job and its effects for a submit event", () => {
    expect(keysToInvalidate({ type: "job", job_id: 9, kind: "submit", target_key: "a12:q7" })).toEqual([
      keys.jobCheck("submit", "a12:q7"),
      keys.job(9),
      keys.studentSubmissions(12, 7),
      keys.studentQuestion(12, 7),
      keys.studentAssignment(12),
      keys.studentAssignments(),
    ]);
  });

  it("covers only the job for kinds without effects", () => {
    expect(keysToInvalidate({ type: "job", job_id: 3, kind: "assignment_summary", target_key: "a5" })).toEqual([
      keys.jobCheck("assignment_summary", "a5"),
      keys.job(3),
    ]);
  });

  it("covers all job and effect prefixes on ready", () => {
    expect(keysToInvalidate({ type: "ready" })).toEqual([["jobCheck"], ["job"], ...ALL_JOB_EFFECT_PREFIXES]);
  });

  it("ignores unknown kinds", () => {
    expect(keysToInvalidate({ type: "job", job_id: 1, kind: "mystery", target_key: "-" })).toEqual([]);
  });
});

describe("parseEvent / handleEvent", () => {
  it("ignores unknown events and bad JSON without throwing", () => {
    expect(parseEvent({ event: "other", data: "{}" })).toBeNull();
    expect(parseEvent({ event: "job", data: "not json" })).toBeNull();
    expect(parseEvent({ event: "job", data: '{"job_id": "x"}' })).toBeNull();
    const qc = new QueryClient();
    expect(() => handleEvent(qc, { event: "job", data: "{" })).not.toThrow();
  });

  it("invalidates the matching jobCheck query and leaves unrelated keys alone", () => {
    const qc = new QueryClient();
    const target = keys.jobCheck("hint", "a1:q2");
    const other = keys.jobCheck("hint", "a1:q3");
    const unrelated = keys.adminClasses();
    for (const key of [target, other, unrelated]) qc.setQueryData(key, { job: null });

    handleEvent(qc, { event: "job", data: JSON.stringify({ job_id: 5, kind: "hint", target_key: "a1:q2" }) });

    expect(qc.getQueryState(target)?.isInvalidated).toBe(true);
    expect(qc.getQueryState(other)?.isInvalidated).toBe(false);
    expect(qc.getQueryState(unrelated)?.isInvalidated).toBe(false);
  });
});
