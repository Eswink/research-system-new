/* global localStorage */
/**
 * WP4.5 视觉对照采集：以原型参考图的同一视口（1440x900；command-center 2560x1440）、
 * dark/normal/zh 偏好渲染产品页面截图，供人工/子代理对照 docs/references/design/
 * console-design/reference/*.png 记录几何差异与残余差。一次性证据脚本，不进入产品。
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(path.resolve("apps/web/package.json"));
const { chromium } = require("@playwright/test");

const BASE = process.env.CAPTURE_BASE ?? "http://127.0.0.1:5173";
const OUT = "scratch/console-reference-recovery/screenshots-20260910";
fs.mkdirSync(OUT, { recursive: true });

const PAGES = [
  { name: "portfolio-projects", hash: "#/portfolio/projects", size: { width: 1440, height: 900 } },
  { name: "plan-protocol", hash: "#/plan/protocol", size: { width: 1440, height: 900 } },
  { name: "evidence-claims", hash: "#/evidence/claims", size: { width: 1440, height: 900 } },
  { name: "govern-budget", hash: "#/govern/budget", size: { width: 1440, height: 900 } },
  { name: "library-endpoints", hash: "#/library/endpoints", size: { width: 1440, height: 900 } },
  { name: "ops-observability", hash: "#/ops/observability", size: { width: 1440, height: 900 } },
  { name: "settings", hash: "#/settings/settings", size: { width: 1440, height: 900 } },
  {
    name: "command-center",
    hash: "#/command-center/command-center",
    size: { width: 2560, height: 1440 },
  },
];

const browser = await chromium.launch({ headless: true });
try {
  for (const page of PAGES) {
    const context = await browser.newContext({
      viewport: page.size,
      reducedMotion: "reduce",
      deviceScaleFactor: 1,
    });
    await context.addInitScript(() => {
      localStorage.setItem(
        "ros.console.preferences",
        JSON.stringify({
          theme: "dark",
          density: "normal",
          language: "zh",
          editorMode: "form",
          version: "capture",
        }),
      );
    });
    const tab = await context.newPage();
    await tab.goto(`${BASE}/?source=example${page.hash}`);
    await tab.waitForTimeout(900);
    await tab.screenshot({ path: `${OUT}/${page.name}-dark-normal-zh.png` });
    console.log("captured", page.name);
    await context.close();
  }
} finally {
  await browser.close();
}
