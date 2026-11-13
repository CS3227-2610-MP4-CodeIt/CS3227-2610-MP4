// Run with Vite at 127.0.0.1:5179: node e2e/complexity.cjs
const { chromium } = require("@playwright/test");
const assert = require("node:assert/strict");

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
  });
  await context.addInitScript(() =>
    localStorage.setItem(
      "auth",
      JSON.stringify({
        token: "test",
        user: {
          id: 1,
          username: "student",
          display_name: "Student",
          role: "student",
        },
      }),
    ),
  );
  const page = await context.newPage();
  const submissions = [
    {
      id: 11,
      verdict: "WRONG_ANSWER",
      passed: 0,
      total: 1,
      created_at: "2026-01-01T12:00:00Z",
      code: 'print("first snapshot")',
    },
    {
      id: 12,
      verdict: "ACCEPTED",
      passed: 1,
      total: 1,
      created_at: "2026-01-02T12:00:00Z",
      code: 'print("second snapshot")',
    },
  ];
  const result = {
    time_complexity: "O(n)",
    space_complexity: "O(1)",
    explanation: "One loop visits each item.",
    assumptions: "Each visit takes constant time.",
  };
  const jobs = {};
  const requests = [];
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (!path.startsWith("/api/")) return route.continue();
    const respond = (data) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(data),
      });
    if (path.endsWith("/events")) return route.abort();
    if (path === "/api/auth/me")
      return respond({
        id: 1,
        username: "student",
        display_name: "Student",
        role: "student",
      });
    if (path === "/api/student/assignments/1")
      return respond({
        id: 1,
        class_id: 1,
        class_name: "Class",
        title: "Assignment",
        description_md: "",
        due_at: null,
        questions: [],
      });
    if (path === "/api/student/assignments/1/questions/2")
      return respond({
        id: 2,
        title: "Question",
        statement_md: "Solve it.",
        difficulty: "easy",
        topics: [],
        time_limit_ms: 1000,
        memory_limit_mb: 128,
        float_tolerance: null,
        test_cases: [],
        solved: false,
      });
    if (path.endsWith("/submissions"))
      return respond(submissions.map(({ code: _code, ...brief }) => brief));
    const match = path.match(/\/submissions\/(\d+)(\/complexity)?$/);
    if (match) {
      const sid = Number(match[1]);
      if (!match[2]) return respond(submissions.find((s) => s.id === sid));
      if (request.method() === "POST") {
        requests.push({ sid, body: request.postData() });
        const fail =
          sid === 12 && requests.filter((r) => r.sid === sid).length === 1;
        const job = {
          id: sid,
          kind: "complexity",
          status: fail ? "failed" : "success",
          result: fail ? null : result,
          error: fail ? "Analysis failed. Try again." : null,
          created_at: "2026-01-01T12:00:00Z",
          finished_at: "2026-01-01T12:00:01Z",
        };
        jobs[sid] = job;
        return respond({ created: true, job });
      }
      return respond({ job: jobs[sid] || null });
    }
    if (/\/(run|submit|hint)$/.test(path)) return respond({ job: null });
    return respond({});
  });
  await page.goto("http://127.0.0.1:5179/student/assignments/1/questions/2");
  await page.locator(".cm-content").click({ timeout: 5000 });
  await page.keyboard.press("Meta+A");
  await page.keyboard.type('print("unsubmitted draft")');
  await page.getByRole("tab", { name: "Submissions" }).click();
  const rows = page.locator("tbody tr");
  await rows.nth(0).getByRole("button").click();
  await page.getByText('print("first snapshot")').waitFor();
  await page.getByRole("button", { name: "Analyze", exact: true }).click();
  await page.getByText("One loop visits each item.").waitFor();
  assert.deepEqual(requests, [{ sid: 11, body: null }]);
  assert.equal(await page.getByText("Auxiliary space").count(), 1);
  await rows.nth(1).getByRole("button").click();
  await page.getByText('print("second snapshot")').waitFor();
  assert.equal(await page.getByText("One loop visits each item.").count(), 0);
  await page.getByRole("button", { name: "Analyze", exact: true }).click();
  await page.getByText("Analysis failed. Try again.").waitFor();
  await page.getByRole("button", { name: "Analyze", exact: true }).click();
  await page.getByText("One loop visits each item.").waitFor();
  assert.deepEqual(requests, [
    { sid: 11, body: null },
    { sid: 12, body: null },
    { sid: 12, body: null },
  ]);
  await page.setViewportSize({ width: 390, height: 844 });
  const panel = page.getByRole("region", { name: "Complexity analysis" });
  await panel.scrollIntoViewIfNeeded();
  const dimensions = await panel.evaluate((el) => ({
    width: el.getBoundingClientRect().width,
    viewport: document.documentElement.clientWidth,
  }));
  assert.ok(dimensions.width <= dimensions.viewport);
  await page.screenshot({
    path: "/tmp/codeit-complexity-mobile.png",
    fullPage: true,
  });
  jobs[11] = {
    id: 100,
    kind: "complexity",
    status: "in_process",
    result: null,
    error: null,
    created_at: "2026-01-01T12:00:00Z",
    finished_at: null,
  };
  await page.reload();
  await page.getByRole("tab", { name: "Submissions" }).click();
  const first = page.locator("tbody tr").nth(0).getByRole("button");
  await first.focus();
  await page.keyboard.press("Enter");
  await page.locator("span.inline-flex").filter({ hasText: "Analyzing…" }).waitFor();
  assert.equal(
    await page
      .getByRole("button", { name: "Analyze", exact: true })
      .isDisabled(),
    true,
  );
  await page.locator("tbody tr").nth(1).getByRole("button").click();
  await page.getByText('print("second snapshot")').waitFor();
  assert.equal(await page.locator("span.inline-flex").filter({ hasText: "Analyzing…" }).count(), 0);
  console.log(
    "PASS: snapshots, isolated results, retry, in-progress switching, keyboard and mobile panel",
  );
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
