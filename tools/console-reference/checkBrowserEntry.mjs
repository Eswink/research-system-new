/* global getComputedStyle */
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire(path.resolve("apps/web/package.json"));
const { chromium } = require("@playwright/test");
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  page.on("pageerror", (error) => console.log("PAGE ERROR:", error.message));
  page.on("console", (message) => {
    if (message.type() === "error") console.log(message.text());
  });
  await page.goto("http://127.0.0.1:5191/?source=example#/portfolio/projects");
  await page.waitForTimeout(2000);
  console.log(
    "GEOMETRY",
    await page.locator('[data-testid^="example-page"]').evaluateAll((nodes) =>
      nodes.map((n) => ({
        id: n.getAttribute("data-testid"),
        rect: n.getBoundingClientRect().toJSON(),
        css: getComputedStyle(n).cssText,
      })),
    ),
  );
  await page.screenshot({ path: "scratch/console-reference/entry-screen.png" });
  console.log("DOM", (await page.locator("body").innerText()).slice(0, 2500));
} finally {
  await browser.close();
}
