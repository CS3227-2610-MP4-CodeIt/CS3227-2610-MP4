import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";

const state = vi.hoisted(() => ({ data: [] as any[] }));
vi.mock("./api", () => ({
  useStudentAssignments: () => ({
    data: state.data,
    isPending: false,
    isError: false,
  }),
  useStudentAssignment: () => ({
    data: state.data[0],
    isPending: false,
    isError: false,
  }),
}));
import { AssignmentsPage } from "./AssignmentsPage";
import { AssignmentPage } from "./AssignmentPage";

const assignment = {
  id: 9,
  class_id: 1,
  class_name: "Algorithms",
  title: "Search",
  due_at: null,
  description_md: "Practice search",
  questions: [
    { id: 3, position: 1, title: "First", difficulty: "easy", solved: true },
    {
      id: 4,
      position: 2,
      title: "Second",
      difficulty: "medium",
      solved: false,
    },
  ],
};
const render = (page: React.ReactNode) =>
  renderToStaticMarkup(<MemoryRouter>{page}</MemoryRouter>);
describe("student assignments", () => {
  it("shows the class, due date, correct progress and assignment link", () => {
    state.data = [assignment];
    const html = render(<AssignmentsPage />);
    expect(html).toContain("Algorithms");
    expect(html).toContain('aria-label="Filter assignments"');
    expect(html).toContain('aria-pressed="true"');
    expect(html).toContain("To do");
    expect(html).toContain("Closed");
    expect(html).toContain("No due date");
    expect(html).toContain("1 of 2 solved");
    expect(html).toContain("In progress");
    expect(html).toContain("width:50%");
    expect(html).toContain("/student/assignments/9");
  });
  it("shows ordered questions, explicit statuses, progress and links", () => {
    state.data = [assignment];
    const html = render(<AssignmentPage />);
    expect(html).toContain("1 / 2");
    expect(html).toContain("width:50%");
    expect(html).toContain("Not solved");
    expect(html).toContain("Solved");
    expect(html.indexOf("First")).toBeLessThan(html.indexOf("Second"));
    expect(html).toContain("/student/assignments/9/questions/4");
    expect(html).not.toContain("Continue to questions");
  });
  it("preserves class and assignment ordering and handles zero and complete progress", () => {
    state.data = [
      {
        ...assignment,
        id: 10,
        class_id: 2,
        class_name: "Zoology",
        title: "Zero",
        due_at: "2000-01-01T00:00:00Z",
        questions: assignment.questions.map((q) => ({ ...q, solved: false })),
      },
      {
        ...assignment,
        id: 11,
        title: "Complete",
        questions: assignment.questions.map((q) => ({ ...q, solved: true })),
      },
      { ...assignment, id: 12, title: "Next", questions: [] },
    ];
    const html = render(<AssignmentsPage />);
    expect(html.indexOf("Algorithms")).toBeLessThan(html.indexOf("Zoology"));
    expect(html.indexOf("Complete")).toBeLessThan(html.indexOf("Next"));
    expect(html).toContain("0 of 2 solved");
    expect(html).toContain("width:0%");
    expect(html).toContain("width:100%");
    expect(html).toContain("Completed");
    expect(html).toContain("2 of 2 solved");
    expect(html).toContain("0 of 0 solved");
    expect(html).toContain("closed");
    expect(html).not.toContain("not started");
  });
  it("handles an empty list and an assignment without a description", () => {
    state.data = [];
    expect(render(<AssignmentsPage />)).toContain("No assignments yet");
    state.data = [{ ...assignment, description_md: "", questions: [] }];
    const html = render(<AssignmentPage />);
    expect(html).not.toContain("About this assignment");
    expect(html).toContain("0 / 0");
  });
  it("shows a single unsolved question and a future due date", () => {
    state.data = [
      {
        ...assignment,
        due_at: "2999-01-01T00:00:00Z",
        questions: [assignment.questions[1]],
      },
    ];
    const list = render(<AssignmentsPage />);
    expect(list).toContain("0 of 1 solved");
    expect(list).toContain("2999");
    expect(list).not.toContain("closed");
    const detail = render(<AssignmentPage />);
    expect(detail).toContain("0 / 1");
    expect(detail).toContain("Not solved");
    expect(detail).toContain("Medium");
  });
  it("shows three questions in supplied order and counts only solved questions", () => {
    state.data = [
      {
        ...assignment,
        questions: [
          ...assignment.questions,
          {
            id: 5,
            position: 3,
            title: "Third",
            difficulty: "hard",
            solved: true,
          },
        ],
      },
    ];
    const detail = render(<AssignmentPage />);
    expect(detail).toContain("2 / 3");
    expect(detail.indexOf("First")).toBeLessThan(detail.indexOf("Second"));
    expect(detail.indexOf("Second")).toBeLessThan(detail.indexOf("Third"));
    expect(detail).toContain("/student/assignments/9/questions/5");
  });
});
