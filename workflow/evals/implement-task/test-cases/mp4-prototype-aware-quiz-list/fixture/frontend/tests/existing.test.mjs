import test from "node:test";
import assert from "node:assert/strict";
import { quizCards } from "../src/quiz-list.mjs";

test("cards preserve order, status actions, and destinations", () => {
  const items = ["not_started", "in_progress", "submitted"].map(
    (attempt_status, index) => ({
      id: index + 1,
      title: "Quiz",
      class_name: "Class",
      question_count: 1,
      attempt_status,
    }),
  );
  const cards = quizCards(items);
  assert.deepEqual(cards.map((card) => card.id), [1, 2, 3]);
  assert.deepEqual(cards.map((card) => card.action), ["Start", "Resume", "View results"]);
  assert.deepEqual(cards.map((card) => card.href), [
    "#/student/attempt/1",
    "#/student/attempt/2",
    "#/student/results/3",
  ]);
});
