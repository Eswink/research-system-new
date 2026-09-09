/* global document, innerWidth */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(path.resolve("apps/web/package.json"));
const { chromium } = require("@playwright/test");
const source = fs.readFileSync("apps/web/src/features/example-console/ExamplePage.tsx", "utf8");
const routes = [...source.matchAll(/"([a-z-]+\/[a-z-]+)"\s*:/g)].map((match) => match[1]);
routes.push("command-center/command-center");
if (new Set(routes).size !== 33) throw new Error("Expected 33 unique example routes");
const selected = process.argv.includes("--all")
  ? routes
  : ["portfolio/projects", "plan/protocol", "evidence/claims", "command-center/command-center"];
const root = process.argv.includes("--recovery")
  ? "scratch/console-reference-recovery"
  : "scratch/console-reference";
const output = `${root}/screenshots`;
fs.mkdirSync(output, { recursive: true });

function inspectPage() {
  return {
    text: document.body.innerText.length,
    overflow: document.body.scrollWidth > innerWidth,
    example: document.querySelector('[data-testid="data-source-badge"]')?.textContent,
    controls: document.querySelectorAll("button, input, select, textarea").length,
    fonts: [...document.fonts]
      .filter((font) => font.status === "loaded")
      .map((font) => font.family),
  };
}

async function captureRoute(browser, route) {
  const page = await browser.newPage({
    viewport: route.startsWith("command-center")
      ? { width: 2560, height: 1440 }
      : { width: 1440, height: 900 },
    reducedMotion: "reduce",
  });
  const row = { route, errors: [], api: [], consoleErrors: [], text: 0 };
  page.setDefaultTimeout(10000);
  page.on("pageerror", (error) => row.errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") row.consoleErrors.push(message.text());
  });
  await page.route(
    (url) => url.pathname.startsWith("/api/"),
    (request) => {
      row.api.push(request.request().url());
      return request.abort();
    },
  );
  try {
    await page.goto(`http://127.0.0.1:5191/?source=example#/${route}`);
    await page.getByTestId(`example-page-${route.replaceAll("/", "-")}`).waitFor();
    if (!route.startsWith("command-center")) {
      await page.locator(`[data-example-loaded="${route}"]`).waitFor({ state: "attached" });
    }
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(output, `${route.replaceAll("/", "-")}.png`) });
    Object.assign(row, await page.evaluate(inspectPage));
  } catch (error) {
    row.errors.push(String(error));
  } finally {
    await page.close();
  }
  console.log(route, `errors=${row.errors.length}`, `api=${row.api.length}`, `chars=${row.text}`);
  return row;
}

const browser = await chromium.launch({ headless: true });
const report = [];
try {
  for (const route of selected) report.push(await captureRoute(browser, route));
} finally {
  await browser.close();
  const serialized = JSON.stringify(report, null, 2);
  const stamp = new Date().toISOString().replaceAll(/[:.]/g, "-");
  fs.writeFileSync(`${root}/browser-smoke-${stamp}.json`, serialized);
  fs.writeFileSync(`${root}/browser-smoke.json`, serialized);
}
if (
  report.length !== selected.length ||
  report.some(
    (row) =>
      row.errors.length ||
      row.api.length ||
      row.consoleErrors.length ||
      row.text < 200 ||
      row.overflow,
  )
)
  process.exitCode = 1;
