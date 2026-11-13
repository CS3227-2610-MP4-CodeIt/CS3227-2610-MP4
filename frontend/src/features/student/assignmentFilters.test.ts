import { describe, expect, it } from "vitest";
import type { StudentAssignment } from "../../api/types";
import { assignmentCategory, filterAssignments } from "./assignmentFilters";

const question = (solved: boolean) => ({
  id: 1,
  position: 1,
  title: "Question",
  difficulty: "easy" as const,
  solved,
});

function assignment(
  id: number,
  due_at: string | null,
  solved: boolean[],
  class_id = 1,
): StudentAssignment {
  return {
    id,
    class_id,
    class_name: `Class ${class_id}`,
    title: `Assignment ${id}`,
    description_md: "",
    due_at,
    questions: solved.map(question),
  };
}

describe("assignment filters", () => {
  it("classifies open work, complete work and closed unfinished work", () => {
    expect(assignmentCategory(assignment(1, null, [false]))).toBe("todo");
    expect(
      assignmentCategory(assignment(2, "2999-01-01T00:00:00Z", [true, false])),
    ).toBe("todo");
    expect(
      assignmentCategory(assignment(3, "2000-01-01T00:00:00Z", [false])),
    ).toBe("closed");
    expect(
      assignmentCategory(assignment(4, "2000-01-01T00:00:00Z", [true])),
    ).toBe("completed");
    expect(assignmentCategory(assignment(5, null, []))).toBe("todo");
  });

  it("retains original newest-first order across classes when filtering", () => {
    const list = [
      assignment(9, null, [false], 2),
      assignment(8, null, [true], 1),
      assignment(7, null, [false], 1),
      assignment(6, "2000-01-01T00:00:00Z", [false], 2),
    ];
    expect(filterAssignments(list, "all").map((item) => item.id)).toEqual([
      9, 8, 7, 6,
    ]);
    expect(filterAssignments(list, "todo").map((item) => item.id)).toEqual([
      9, 7,
    ]);
    expect(filterAssignments(list, "completed").map((item) => item.id)).toEqual(
      [8],
    );
    expect(filterAssignments(list, "closed").map((item) => item.id)).toEqual([
      6,
    ]);
  });
});
