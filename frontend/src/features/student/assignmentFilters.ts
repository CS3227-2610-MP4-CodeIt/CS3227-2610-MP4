import type { StudentAssignment } from "../../api/types";
import { isPastDue } from "./verdict";

export type AssignmentFilter = "all" | "todo" | "completed" | "closed";

/** Completed work stays completed even after its due date. */
export function assignmentCategory(
  assignment: StudentAssignment,
): Exclude<AssignmentFilter, "all"> {
  const questions = assignment.questions;
  if (questions.length > 0 && questions.every((question) => question.solved)) {
    return "completed";
  }
  return isPastDue(assignment.due_at) ? "closed" : "todo";
}

export function filterAssignments(
  assignments: StudentAssignment[],
  filter: AssignmentFilter,
): StudentAssignment[] {
  return filter === "all"
    ? assignments
    : assignments.filter(
        (assignment) => assignmentCategory(assignment) === filter,
      );
}
