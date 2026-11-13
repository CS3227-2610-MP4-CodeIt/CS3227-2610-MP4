// With Vite at 127.0.0.1:5179: node e2e/admin-summary.cjs
// All API requests are mocked; no backend or AI provider is contacted.
const { chromium, expect } = require("@playwright/test");

const user = (id) => ({
  id,
  username: `admin${id}`,
  display_name: `Admin ${id}`,
  role: "admin",
});
const auth = (id) => ({ token: `test-${id}`, user: user(id) });
const result = (name, students) => ({
  summary_md: name,
  stats: {
    assignment: { title: "Assignment", class_name: "Class", due_at: null },
    students_in_class: students,
    students_attempted_any: 1,
    students_solved_all: 0,
    questions: [],
  },
});
const job = (id, status, data = null) => ({
  id,
  kind: "assignment_summary",
  status,
  result: data,
  error: status === "failed" ? "Synthetic generation failure" : null,
  created_at: "2026-11-13T01:00:00Z",
  finished_at: status === "in_process" ? null : "2026-11-13T01:01:00Z",
});

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
  });
  try {
    const context = await browser.newContext();
    await context.addInitScript(() => {
      // Test-only auth seeding; production retention never uses browser storage.
      if (!localStorage.getItem("auth"))
        localStorage.setItem(
          "auth",
          JSON.stringify({
            token: "test-1",
            user: {
              id: 1,
              username: "admin1",
              display_name: "Admin 1",
              role: "admin",
            },
          }),
        );
    });
    const page = await context.newPage();
    page.on("pageerror", (error) =>
      console.error("Browser error:", error.message),
    );
    let adminId = 1;
    const jobs = {
      1: job(1, "success", result("Original summary", 10)),
      2: null,
    };
    let checkError = false;
    let networkCheckError = false;
    let postError = false;
    await page.route("**/api/**", async (route) => {
      const request = route.request();
      const path = new URL(request.url()).pathname;
      if (!path.startsWith("/api/")) return route.continue();
      const respond = (data, status = 200) =>
        route.fulfill({
          status,
          contentType: "application/json",
          body: JSON.stringify(data),
        });
      if (path === "/api/events")
        return route.fulfill({
          contentType: "text/event-stream",
          body: "event: ready\ndata: {}\n\n",
        }); // Reconnect/ready refetches drive controlled status changes.
      if (path === "/api/health/ready") return respond({ status: "ok" });
      if (path === "/api/auth/me") return respond(user(adminId));
      if (path === "/api/admin/users") return respond([]);
      if (path === "/api/admin/classes/1")
        return respond({
          id: 1,
          name: "Class",
          teachers: [],
          students: [],
          assignments: [1, 2].map((id) => ({
            id,
            title: `Assignment ${id}`,
            due_at: null,
          })),
        });
      const match = path.match(/^\/api\/admin\/assignments\/(\d+)\/summary$/);
      if (match) {
        const aid = Number(match[1]);
        if (request.method() === "POST") {
          if (postError)
            return respond({ detail: "Synthetic request failure" }, 400);
          jobs[aid] = job((jobs[aid]?.id ?? 0) + 1, "in_process");
          return respond({ created: true, job: jobs[aid] }, 202);
        }
        if (networkCheckError) return route.abort();
        if (checkError)
          return respond({ detail: "Synthetic check failure" }, 400);
        return respond({ job: jobs[aid] });
      }
      return respond({ detail: `Unexpected mocked endpoint: ${path}` }, 404);
    });
    const navigate = (aid) =>
      page.evaluate((id) => {
        history.pushState(null, "", `/admin/classes/1/assignments/${id}`);
        dispatchEvent(new PopStateEvent("popstate"));
      }, aid);
    const previous = page.getByText(/Previous successful result — generated/);
    const regenerate = page.getByRole("button", {
      name: "Regenerate summary",
      exact: true,
    });
    await page.goto("http://127.0.0.1:5179/admin/classes/1/assignments/1");
    await expect(page.getByText("Original summary", { exact: true }))
      .toBeVisible()
      .catch(async (error) => {
        console.error("Mock page:", await page.locator("body").innerText());
        throw error;
      });
    await expect(previous).toHaveCount(0);
    await regenerate.click();
    await expect(previous).toBeVisible();
    await expect(regenerate).toBeDisabled();
    await expect(
      page.getByText("Original summary", { exact: true }),
    ).toBeVisible();
    const label = await previous.textContent();
    const timestamp = await page.evaluate(() =>
      new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date("2026-11-13T01:01:00Z")),
    );
    expect(label).toContain(timestamp);
    expect(label).toContain("Statistics reflect that generation.");
    jobs[1] = job(2, "success", result("Replacement summary", 20));
    await expect(
      page.getByText("Replacement summary", { exact: true }),
    ).toBeVisible();
    await expect(page.getByText(/20 students in class/)).toBeVisible();
    await expect(
      page.getByText("Original summary", { exact: true }),
    ).toHaveCount(0);
    await expect(previous).toHaveCount(0);

    // Late older success must not overwrite the newer displayed success.
    jobs[1] = job(1, "success", result("Late old summary", 5));
    await page.waitForResponse(
      (response) =>
        response.url().endsWith("/assignments/1/summary") &&
        response.request().method() === "GET",
    );
    await expect(
      page.getByText("Replacement summary", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Late old summary", { exact: true }),
    ).toHaveCount(0);
    jobs[1] = job(2, "success", result("Replacement summary", 20));
    await regenerate.click();
    jobs[1] = job(3, "failed");
    await expect(
      page.getByText("Synthetic generation failure", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText(
        "Regeneration failed. Showing the previous successful result.",
      ),
    ).toBeVisible();
    await expect(
      page.getByText("Replacement summary", { exact: true }),
    ).toBeVisible();
    await expect(page.getByText(/20 students in class/)).toBeVisible();

    checkError = true;
    await expect(
      page.getByText("Synthetic check failure", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Replacement summary", { exact: true }),
    ).toBeVisible();
    checkError = false;
    await expect(
      page.getByText("Synthetic check failure", { exact: true }),
    ).toHaveCount(0);
    networkCheckError = true;
    await expect(
      page.getByText("Could not reach the server. Try again.", {
        exact: false,
      }),
    ).toBeVisible({ timeout: 15000 });
    await expect(
      page.getByText("Replacement summary", { exact: true }),
    ).toBeVisible();
    networkCheckError = false;
    await expect(
      page.getByText("Could not reach the server. Try again.", {
        exact: false,
      }),
    ).toHaveCount(0);
    postError = true;
    await regenerate.click();
    await expect(
      page.getByText("Synthetic request failure", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Replacement summary", { exact: true }),
    ).toBeVisible();
    postError = false;

    // A later success (for example from another tab) is not made "previous"
    // by the older mutation's request error.
    jobs[1] = job(4, "success", result("Recovered summary", 25));
    await expect(
      page.getByText("Recovered summary", { exact: true }),
    ).toBeVisible();
    await expect(previous).toHaveCount(0);
    jobs[1] = job(5, "failed");
    await expect(previous).toBeVisible();

    // Assignment change without a document reload must reset retained state.
    await navigate(2);
    await expect(
      page.getByText("No summary yet.", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Replacement summary", { exact: true }),
    ).toHaveCount(0);
    await page
      .getByRole("button", { name: "Generate summary", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Regenerate summary", exact: true }),
    ).toBeDisabled();
    jobs[2] = job(4, "failed");
    await expect(
      page.getByText("Synthetic generation failure", { exact: true }),
    ).toBeVisible();
    await expect(previous).toHaveCount(0);
    await navigate(1);
    await expect(
      page.getByRole("heading", { name: "Assignment 1", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Replacement summary", { exact: true }),
    ).toHaveCount(0);

    // Reload after failed regeneration cannot rediscover an earlier success.
    await page.reload();
    await expect(
      page.getByText("Synthetic generation failure", { exact: true }),
    ).toBeVisible();
    await expect(previous).toHaveCount(0);

    jobs[1] = job(6, "success", result("Admin one private result", 30));
    await expect(
      page.getByText("Admin one private result", { exact: true }),
    ).toBeVisible();
    adminId = 2;
    jobs[1] = job(7, "failed");
    await page.evaluate((next) => {
      const value = JSON.stringify(next);
      localStorage.setItem("auth", value);
      dispatchEvent(
        new StorageEvent("storage", { key: "auth", newValue: value }),
      );
    }, auth(2));
    await expect(page.getByText("Admin 2", { exact: false })).toBeVisible();
    await navigate(1);
    await expect(
      page.getByText("Synthetic generation failure", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Admin one private result", { exact: true }),
    ).toHaveCount(0);
    await expect(previous).toHaveCount(0);
    console.log(
      "PASS: initial success, replacement, failure, request/check errors, isolation, older jobs and remount limitation",
    );
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
