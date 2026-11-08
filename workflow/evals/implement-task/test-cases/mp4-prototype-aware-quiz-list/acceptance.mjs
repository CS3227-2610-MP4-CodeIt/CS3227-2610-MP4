import {createRequire} from "node:module";
import path from "node:path";
import {pathToFileURL} from "node:url";

const workspace = path.resolve(process.argv[2]);
const evidenceDir = path.resolve(process.argv[3]);
const projectRoot = path.resolve(process.env.EVAL_PROJECT_ROOT);
const hostFrontend = path.join(projectRoot, "frontend");
const requireFromFrontend = createRequire(path.join(hostFrontend, "package.json"));
const results = {functional: [], desktop: [], mobile: [], infrastructure_error: null};

function record(group, id, passed, detail) {
  results[group].push({id, pass: Boolean(passed), detail: String(detail)});
}

function relativeDifference(a, b) {
  return Math.abs(a - b);
}

async function pageMetrics(page) {
  const role = (name, options = {}) => page.getByRole(name, options);
  const main = role("main");
  const heading = role("heading", {name: "My quizzes", level: 1});
  const search = role("searchbox", {name: "Search quizzes"});
  const cardHeadings = role("heading", {level: 2});
  const rect = async (locator) => locator.evaluate((element) => {
    const box = element.getBoundingClientRect();
    return {x: box.x, y: box.y, width: box.width, height: box.height};
  });
  const color = async (locator, property) => locator.evaluate(
    (element, cssProperty) => getComputedStyle(element)[cssProperty], property,
  );
  const cards = [];
  for (let index = 0; index < await cardHeadings.count(); index += 1) {
    cards.push(await cardHeadings.nth(index).evaluate((headingElement) => {
      const viewportWidth = window.innerWidth;
      let element = headingElement.parentElement;
      let candidate = null;
      while (element && element.tagName !== "MAIN") {
        const box = element.getBoundingClientRect();
        if (box.width >= Math.min(200, viewportWidth * 0.65) && box.height >= 120) {
          candidate = element;
          break;
        }
        element = element.parentElement;
      }
      const measured = candidate ?? headingElement;
      const box = measured.getBoundingClientRect();
      return {
        x: box.x, y: box.y, width: box.width, height: box.height,
        backgroundColor: getComputedStyle(measured).backgroundColor,
      };
    }));
  }
  const action = role("link", {name: "Start"}).first();
  const documentWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  return {
    boxes: {
      main: await rect(main),
      heading: await rect(heading),
      search: await rect(search),
      cards,
    },
    colors: {
      page: await page.locator("body").evaluate((element) => getComputedStyle(element).backgroundColor),
      card: cards[0]?.backgroundColor ?? "unavailable",
      action: await color(action, "backgroundColor"),
    },
    documentWidth,
    viewportWidth: await page.evaluate(() => window.innerWidth),
  };
}

function compareMetrics(reference, actual, viewport, group) {
  const failures = [];
  const tolerance = viewport.width <= 620 ? 9 : 12;
  for (const key of ["main", "heading", "search"]) {
    for (const dimension of ["x", "y", "width", "height"]) {
      const difference = relativeDifference(reference.boxes[key][dimension], actual.boxes[key][dimension]);
      if (difference > tolerance) {
        failures.push(`${key}.${dimension} differs by ${difference.toFixed(1)}px (limit ${tolerance}px)`);
      }
    }
  }
  if (reference.boxes.cards.length !== actual.boxes.cards.length) {
    failures.push(`expected ${reference.boxes.cards.length} visible cards; found ${actual.boxes.cards.length}`);
  }
  for (let index = 0; index < Math.min(reference.boxes.cards.length, actual.boxes.cards.length); index += 1) {
    for (const dimension of ["x", "y", "width", "height"]) {
      const difference = relativeDifference(reference.boxes.cards[index][dimension], actual.boxes.cards[index][dimension]);
      if (difference > tolerance) {
        failures.push(`card ${index + 1} ${dimension} differs by ${difference.toFixed(1)}px (limit ${tolerance}px)`);
      }
    }
  }
  for (const key of ["page", "card", "action"]) {
    if (reference.colors[key] !== actual.colors[key]) {
      failures.push(`${key} color differs from the approved prototype`);
    }
  }
  const rows = (cards) => new Set(cards.map((card) => Math.round(card.y))).size;
  const expectedRows = viewport.width <= 620 ? reference.boxes.cards.length : Math.ceil(reference.boxes.cards.length / 2);
  if (rows(actual.boxes.cards) !== expectedRows) {
    failures.push(`expected about ${expectedRows} card row(s); found ${rows(actual.boxes.cards)}`);
  }
  if (actual.documentWidth > actual.viewportWidth) failures.push("page has horizontal overflow");
  record(group, "prototype-layout", failures.length === 0,
    failures.length ? failures.join("; ") : `Rendered geometry, colors and card arrangement match the prototype within ${tolerance}px.`);
}

async function run() {
  const {chromium} = requireFromFrontend("playwright");
  const vitePath = requireFromFrontend.resolve("vite");
  const reactPluginPath = requireFromFrontend.resolve("@vitejs/plugin-react");
  const [{createServer}, reactPluginModule] = await Promise.all([
    import(pathToFileURL(vitePath)),
    import(pathToFileURL(reactPluginPath)),
  ]);
  const reactPlugin = reactPluginModule.default;
  const server = await createServer({
    configFile: false,
    root: path.join(workspace, "frontend"),
    plugins: [reactPlugin()],
    resolve: {
      alias: [
        {find: "react-dom/client", replacement: requireFromFrontend.resolve("react-dom/client")},
        {find: "react/jsx-dev-runtime", replacement: requireFromFrontend.resolve("react/jsx-dev-runtime")},
        {find: "react/jsx-runtime", replacement: requireFromFrontend.resolve("react/jsx-runtime")},
        {find: "react", replacement: requireFromFrontend.resolve("react")},
      ],
    },
    server: {host: "127.0.0.1", port: 0, strictPort: false, fs: {allow: [workspace, hostFrontend]}},
    logLevel: "error",
  });
  const prototypeUrl = pathToFileURL(path.join(workspace, "frontend/prototype/selected.html")).href;
  let browser;
  try {
    await server.listen();
    const appUrl = server.resolvedUrls.local[0];
    browser = await chromium.launch({headless: true});

    const desktopViewport = {width: 1280, height: 900};
    const context = await browser.newContext({viewport: desktopViewport, serviceWorkers: "block"});
    await context.route("**/*", (route) => {
      const url = new URL(route.request().url());
      if (url.protocol === "file:" || (url.protocol === "http:" && url.hostname === "127.0.0.1")) {
        return route.continue();
      }
      return route.abort();
    });
    const app = await context.newPage();
    const prototype = await context.newPage();
    app.setDefaultTimeout(1500);
    prototype.setDefaultTimeout(1500);
    const pageErrors = [];
    app.on("pageerror", (error) => pageErrors.push(error.message));
    app.on("response", async (response) => {
      if (response.status() >= 400) {
        pageErrors.push(`${response.status()} ${response.url()}: ${(await response.text().catch(() => "")).slice(0, 1200)}`);
      }
    });
    app.on("console", (message) => {
      if (message.type() === "error") pageErrors.push(message.text());
    });
    const [, prototypeResponse] = await Promise.all([app.goto(appUrl), prototype.goto(prototypeUrl)]);
    if (prototypeResponse && prototypeResponse.status() >= 400) {
      throw new Error(`Approved prototype failed to load: HTTP ${prototypeResponse.status()}`);
    }
    const headingReady = await app.getByRole("heading", {name: "My quizzes", level: 1})
      .waitFor({timeout: 5000}).then(() => true).catch(() => false);
    if (!headingReady) {
      record("functional", "app-renders", false,
        `Expected the My quizzes heading; body=${(await app.locator("body").innerText().catch(() => "<unreadable>")).slice(0, 500)}; browserErrors=${JSON.stringify(pageErrors)}`);
      for (const group of ["desktop", "mobile"]) {
        record(group, "prototype-layout", false, "App did not render, so its layout could not be compared.");
      }
      return;
    }

    const cards = app.getByRole("heading", {level: 2});
    const initialTitles = await cards.allTextContents();
    const actions = await app.getByRole("link").allTextContents();
    const hrefs = await app.getByRole("link").evaluateAll((links) => links.map((link) => link.getAttribute("href")));
    const baseBehavior = initialTitles.join("|") === "Arrays|Trees|Regex a[|Graphs"
      && actions.join("|") === "Start|Resume|View results|Start"
      && JSON.stringify(hrefs) === JSON.stringify([
        "#/student/attempt/7", "#/student/attempt/3", "#/student/results/9", "#/student/attempt/12",
      ]);
    record("functional", "initial-cards-and-actions", baseBehavior,
      `titles=${JSON.stringify(initialTitles)} actions=${JSON.stringify(actions)} hrefs=${JSON.stringify(hrefs)}`);

    const search = app.getByRole("searchbox", {name: "Search quizzes"});
    let matchingTitles = [];
    async function searchCheck(id, query, expected, detail) {
      try {
        await search.fill(query);
        matchingTitles = await cards.allTextContents();
        record("functional", id, matchingTitles.join("|") === expected,
          `${detail}; visible titles=${JSON.stringify(matchingTitles)}`);
      } catch (error) {
        record("functional", id, false, `${detail}; interaction failed: ${error.message}`);
      }
    }
    await searchCheck("trimmed-case-insensitive-title-search", "  TrEeS ", "Trees", "Search trims whitespace and ignores case");
    await searchCheck("course-name-search-preserves-order", "alpha", "Arrays|Regex a[", "Search also matches course names and preserves source order");
    await searchCheck("literal-search-text", "a[", "Regex a[", "Search treats regex metacharacters literally");

    let clearButton;
    let clearControlNames = [];
    try {
      await search.fill("not-a-quiz");
      const emptyCount = await cards.count();
      const emptyMessage = await app.getByText("No quizzes match your search.").isVisible().catch(() => false);
      const buttons = app.getByRole("button");
      clearControlNames = await buttons.allTextContents();
      const clearIndex = clearControlNames.findIndex((name) => /clear|reset/i.test(name));
      clearButton = clearIndex >= 0 ? buttons.nth(clearIndex) : null;
      const nativeSearchInput = await search.evaluate((input) => input instanceof HTMLInputElement && input.type === "search");
      record("functional", "no-results-and-clear-control", emptyCount === 0 && emptyMessage,
        `cards=${emptyCount} message=${emptyMessage}; visible button labels=${JSON.stringify(clearControlNames)}; native search input=${nativeSearchInput}`);
    } catch (error) {
      record("functional", "no-results-and-clear-control", false, `Interaction failed: ${error.message}`);
    }
    try {
      if (clearButton) await clearButton.click({timeout: 1000});
      else await search.press("Escape");
      let resetTitles = await cards.allTextContents();
      if (resetTitles.length === 0) {
        await search.fill("");
        resetTitles = await cards.allTextContents();
      }
      record("functional", "clear-restores-list", resetTitles.join("|") === "Arrays|Trees|Regex a[|Graphs",
        `visible titles=${JSON.stringify(resetTitles)}`);
    } catch (error) {
      record("functional", "clear-restores-list", false, `Interaction failed: ${error.message}`);
    }

    // Restore a stable full-list state even when the clear interaction fails;
    // layout evidence should not depend on an earlier functional assertion.
    await search.fill("").catch(() => {});
    const desktopReferenceMetrics = await pageMetrics(prototype);
    try {
      const desktopAppMetrics = await pageMetrics(app);
      compareMetrics(desktopReferenceMetrics, desktopAppMetrics, desktopViewport, "desktop");
    } catch (error) {
      record("desktop", "prototype-layout", false, `Layout metrics unavailable: ${error.message}`);
    }
    await prototype.screenshot({path: path.join(evidenceDir, "prototype-desktop.png")});
    await app.screenshot({path: path.join(evidenceDir, "implementation-desktop.png")});

    const mobileViewport = {width: 390, height: 844};
    await Promise.all([app.setViewportSize(mobileViewport), prototype.setViewportSize(mobileViewport)]);
    await Promise.all([app.goto(appUrl), prototype.goto(prototypeUrl)]);
    await app.getByRole("heading", {name: "My quizzes", level: 1}).waitFor();
    try {
      compareMetrics(await pageMetrics(prototype), await pageMetrics(app), mobileViewport, "mobile");
    } catch (error) {
      record("mobile", "prototype-layout", false, `Layout metrics unavailable: ${error.message}`);
    }
    await app.screenshot({path: path.join(evidenceDir, "implementation-mobile.png"), fullPage: true});
  } finally {
    if (browser) await browser.close();
    await server.close();
  }
}

try {
  const workspace = path.resolve(process.argv[2]);
  const evidenceDir = path.resolve(process.argv[3]);
  await import("node:fs/promises").then(({mkdir}) => mkdir(evidenceDir, {recursive: true}));
  await run();
} catch (error) {
  results.infrastructure_error = error?.stack || String(error);
}

process.stdout.write(`${JSON.stringify(results)}\n`);
