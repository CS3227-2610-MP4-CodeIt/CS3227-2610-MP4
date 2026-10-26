import { describe, expect, it } from "vitest";
import { ApiError } from "../../api/client";
import { checkQuestion, emptyForm, moveItem, newRow, parseTopics, questionErrors, toQuestionIn } from "./questionForm";

const validForm = () => ({ ...emptyForm(), title: "Sum", statement_md: "Add two numbers." });

describe("parseTopics", () => {
  it("trims, lower-cases and de-duplicates, dropping empty entries", () => {
    expect(parseTopics(" BFS, trees,, bfs ,Graphs ")).toEqual(["bfs", "trees", "graphs"]);
  });
});

describe("checkQuestion", () => {
  it("accepts a valid form", () => {
    expect(checkQuestion(validForm())).toEqual([]);
  });

  it("needs a visible and a hidden test case", () => {
    const f = { ...validForm(), test_cases: [newRow(false), newRow(false)] };
    expect(checkQuestion(f)).toContain("At least one test case must be hidden.");
    const g = { ...validForm(), test_cases: [newRow(true), newRow(true)] };
    expect(checkQuestion(g)).toContain("At least one test case must be visible.");
  });

  it("needs 2–50 test cases", () => {
    expect(checkQuestion({ ...validForm(), test_cases: [newRow(true)] })).toContain(
      "A question needs 2–50 test cases.",
    );
    const many = Array.from({ length: 51 }, (_, i) => newRow(i % 2 === 0));
    expect(checkQuestion({ ...validForm(), test_cases: many })).toContain("A question needs 2–50 test cases.");
  });

  it("checks title, statement, topics and limits", () => {
    const problems = checkQuestion({
      ...validForm(),
      title: "x".repeat(201),
      statement_md: " ",
      topics: "a, b, c, d, e, f",
      time_limit_ms: "50",
      tolerance: true,
      tol_abs: "0",
      tol_rel: "0",
    });
    expect(problems).toEqual([
      "Title must be 1–200 characters.",
      "Statement must be 1–20 000 characters.",
      "At most 5 topics.",
      "Time limit must be 100–10 000 ms.",
      "At least one tolerance must be above 0.",
    ]);
  });
});

describe("toQuestionIn", () => {
  it("normalises topics, converts numbers and drops row keys", () => {
    const body = toQuestionIn({ ...validForm(), topics: "Math, math", tolerance: true, tol_abs: "0.001" });
    expect(body.topics).toEqual(["math"]);
    expect(body.time_limit_ms).toBe(2000);
    expect(body.float_tolerance).toEqual({ abs: 0.001, rel: 0 });
    expect(body.test_cases[0]).toEqual({ stdin: "", expected_stdout: "", is_hidden: false });
  });

  it("sends no tolerance when it is off", () => {
    expect(toQuestionIn(validForm()).float_tolerance).toBeNull();
  });
});

describe("questionErrors", () => {
  it("maps 422 items to rows and fields by loc", () => {
    const err = new ApiError(422, [
      { loc: ["body", "test_cases", 3, "expected_stdout"], msg: "too large" },
      { loc: ["body", "title"], msg: "too short" },
      { loc: ["body"], msg: "at least one hidden test case is required" },
    ]);
    expect(questionErrors(err)).toEqual({
      fields: { title: "too short" },
      rows: { 3: "expected_stdout: too large" },
      other: ["at least one hidden test case is required"],
    });
  });

  it("ignores non-422 errors", () => {
    expect(questionErrors(new ApiError(409, "in use"))).toEqual({ fields: {}, rows: {}, other: [] });
  });
});

describe("moveItem", () => {
  it("swaps neighbours and ignores moves past the ends", () => {
    expect(moveItem([1, 2, 3], 0, 1)).toEqual([2, 1, 3]);
    expect(moveItem([1, 2, 3], 2, -1)).toEqual([1, 3, 2]);
    const items = [1, 2];
    expect(moveItem(items, 0, -1)).toBe(items);
  });
});
