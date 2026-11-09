import { describe, expect, it } from "vitest";
import { jobUrl, targetKey } from "./endpoints";

describe("submission complexity jobs", () => {
  it("addresses a single submitted snapshot", () => {
    const key = targetKey.submission(12, 7, 3);
    expect(jobUrl("complexity", key)).toBe(
      "/student/assignments/12/questions/7/submissions/3/complexity",
    );
    expect(() => jobUrl("complexity", targetKey.question(12, 7))).toThrow();
  });
});
