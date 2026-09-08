// capture-reference.mjs — 生成设计参考图（PLAN-20260908-034 T01）
//
// 用 Playwright 加载已 pin 的参考预览，逐页截图到 ../reference/。
// 主图集：dark × normal × zh-CN（33 页规范路由中的 31 个设计页 + 大屏）。
// 高风险页（protocol/endpoints/timeline/approvals/claims/cost）另采
// 双主题 × 双密度 × 双语 8 组合。
//
// 用法：node capture-reference.mjs [--only <pageId>]
// 依赖：apps/web 的 @playwright/test（通过 NODE_PATH 注入）。

import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Playwright 由 apps/web 的 devDependencies 提供；参考预览不另装依赖。
const { chromium } = await import(
  new URL("../../../../../apps/web/node_modules/@playwright/test/index.mjs", import.meta.url).href
);

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REF_DIR = path.join(HERE, "..", "reference");

const MIME = {
  ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript",
  ".css": "text/css", ".jsx": "text/javascript", ".woff2": "font/woff2",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg",
};

function serve(dir, port) {
  const server = createServer(async (req, res) => {
    const urlPath = decodeURIComponent(new URL(req.url, "http://x").pathname);
    const target = path.join(dir, urlPath === "/" ? "App.html" : urlPath);
    try {
      const body = await readFile(target);
      res.writeHead(200, { "Content-Type": MIME[path.extname(target)] ?? "application/octet-stream" });
      res.end(body);
    } catch {
      res.writeHead(404).end("not found");
    }
  });
  return new Promise((resolve) => server.listen(port, "127.0.0.1", () => resolve(server)));
}

/** 31 个设计页（domain/tab 经 localStorage 种子设定）。 */
const PAGES = [
  ["plan-overview", { domain: "plan", tab: "overview" }],
  ["plan-protocol", { domain: "plan", tab: "protocol" }],
  ["plan-team", { domain: "plan", tab: "team" }],
  ["portfolio-projects", { domain: "portfolio", tab: "projects" }],
  ["portfolio-experiments", { domain: "portfolio", tab: "experiments" }],
  ["portfolio-runs-history", { domain: "portfolio", tab: "runs-history" }],
  ["portfolio-compare", { domain: "portfolio", tab: "compare" }],
  ["run-timeline", { domain: "run", tab: "timeline" }],
  ["run-approvals", { domain: "run", tab: "approvals" }],
  ["run-workspace", { domain: "run", tab: "workspace" }],
  ["library-prompts", { domain: "library", tab: "prompts" }],
  ["library-datasets", { domain: "library", tab: "datasets" }],
  ["library-notebooks", { domain: "library", tab: "notebooks" }],
  ["library-model-registry", { domain: "library", tab: "model-registry" }],
  ["library-lineage", { domain: "library", tab: "lineage" }],
  ["library-endpoints", { domain: "library", tab: "endpoints" }],
  ["library-setup", { domain: "library", tab: "setup" }],
  ["evidence-claims", { domain: "evidence", tab: "claims" }],
  ["insights-reports", { domain: "insights", tab: "reports" }],
  ["insights-cost-analytics", { domain: "insights", tab: "cost-analytics" }],
  ["ops-alerts", { domain: "ops", tab: "alerts" }],
  ["ops-incidents", { domain: "ops", tab: "incidents" }],
  ["ops-schedules", { domain: "ops", tab: "schedules" }],
  ["ops-integrations", { domain: "ops", tab: "integrations" }],
  ["ops-data-health", { domain: "ops", tab: "data-health" }],
  ["ops-matrix", { domain: "ops", tab: "matrix" }],
  ["govern-budget", { domain: "govern", tab: "budget" }],
  ["govern-audit", { domain: "govern", tab: "audit" }],
  ["settings", { domain: "__settings" }],
  ["notifications", { domain: "__notifications" }],
];

/** 高风险页的 8 组合完整覆盖。 */
const HIGH_RISK = new Set([
  "plan-protocol", "library-endpoints", "run-timeline",
  "run-approvals", "evidence-claims", "insights-cost-analytics",
]);

const COMBOS = [];
for (const theme of ["dark", "light"]) {
  for (const density of ["normal", "compact"]) {
    for (const lang of ["zh-CN", "en"]) {
      COMBOS.push({ theme, density, lang });
    }
  }
}

async function capturePage(browser, port, id, seed, combo, suffix) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });
  await context.addInitScript((s) => {
    localStorage.setItem("ros.lang", s.lang);
    if (s.domain) localStorage.setItem("ros.domain", s.domain);
    if (s.tab) localStorage.setItem("ros.tab", s.tab);
  }, { lang: combo.lang, ...seed });
  const page = await context.newPage();
  await page.goto(`http://127.0.0.1:${port}/App.html`, { waitUntil: "load" });
  await page.waitForSelector("aside", { timeout: 15000 });
  // 等待 boot 遮罩动画与 babel 转译完成
  await page.waitForTimeout(2600);
  await page.evaluate((c) => {
    document.documentElement.dataset.theme = c.theme;
    document.documentElement.dataset.density = c.density;
  }, combo);
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(REF_DIR, `${id}${suffix}.png`) });
  await context.close();
}

async function captureCommandCenter(browser, port) {
  const context = await browser.newContext({
    viewport: { width: 2560, height: 1440 },
    deviceScaleFactor: 1,
  });
  await context.addInitScript(() => localStorage.setItem("ros.lang", "zh-CN"));
  const page = await context.newPage();
  await page.goto(`http://127.0.0.1:${port}/Command%20Center.html`, { waitUntil: "load" });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(REF_DIR, "command-center.png") });
  await context.close();
}

const only = process.argv.indexOf("--only");
const onlyId = only >= 0 ? process.argv[only + 1] : null;

const server = await serve(HERE, 5199);
const browser = await chromium.launch();
try {
  const { mkdir } = await import("node:fs/promises");
  await mkdir(REF_DIR, { recursive: true });
  const primary = { theme: "dark", density: "normal", lang: "zh-CN" };
  for (const [id, seed] of PAGES) {
    if (onlyId && onlyId !== id) continue;
    await capturePage(browser, 5199, id, seed, primary, "");
    if (HIGH_RISK.has(id)) {
      for (const combo of COMBOS) {
        if (combo.theme === "dark" && combo.density === "normal" && combo.lang === "zh-CN") continue;
        await capturePage(browser, 5199, id, seed, combo, `--${combo.theme}-${combo.density}-${combo.lang === "zh-CN" ? "zh" : "en"}`);
      }
    }
    process.stdout.write(`captured ${id}\n`);
  }
  if (!onlyId || onlyId === "command-center") {
    await captureCommandCenter(browser, 5199);
    process.stdout.write("captured command-center\n");
  }
} finally {
  await browser.close();
  server.close();
}
