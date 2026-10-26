import { describe, expect, it } from "vitest";
import { fromLocalInput, toLocalInput } from "./dates";

describe("datetime-local conversion", () => {
  it("round-trips a UTC ISO time through the local input value", () => {
    const iso = "2026-11-02T15:30:00.000Z";
    expect(fromLocalInput(toLocalInput(iso))).toBe(iso);
  });

  it("maps an empty input to null", () => {
    expect(fromLocalInput("")).toBeNull();
  });
});
