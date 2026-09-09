/* global document, localStorage, getComputedStyle */
import { createServer } from "node:http";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire(path.resolve("apps/web/package.json"));
const { chromium } = require("@playwright/test");
const root = path.resolve("docs/references/design/console-design/preview");
const mime = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".jsx": "text/javascript",
  ".css": "text/css",
  ".woff2": "font/woff2",
};
const server = createServer((req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
    const file = path.resolve(root, "." + pathname);
    if (!file.startsWith(root + path.sep)) {
      res.writeHead(403).end();
      return;
    }
    res
      .writeHead(200, { "Content-Type": mime[path.extname(file)] ?? "application/octet-stream" })
      .end(fs.readFileSync(file));
  } catch {
    res.writeHead(404).end();
  }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const browser = await chromium.launch({ headless: true });
const port = server.address().port;
const output = "scratch/console-reference/layout-comparison";
fs.mkdirSync(output, { recursive: true });
const result = {};
try {
  for (const mode of ["source", "native"]) {
    const page = await browser.newPage({
      viewport: { width: 1440, height: 900 },
      reducedMotion: "reduce",
    });
    await page.addInitScript(() => {
      localStorage.setItem("ros.lang", "zh-CN");
      localStorage.setItem("ros.domain", "portfolio");
      localStorage.setItem("ros.tab", "projects");
    });
    page.on("pageerror", (e) => console.log(mode, "ERROR", e.message));
    await page.goto(
      mode === "source"
        ? `http://127.0.0.1:${port}/App.html`
        : "http://127.0.0.1:5191/?source=example#/portfolio/projects",
    );
    await page.waitForTimeout(mode === "source" ? 2800 : 500);
    await page.evaluate(() => document.fonts.ready);
    result[mode] = await page.evaluate(() => {
      const describe = (n) => {
        const c = getComputedStyle(n);
        return {
          text: n.textContent.slice(0, 130),
          classes: n.className,
          rect: n.getBoundingClientRect().toJSON(),
          display: c.display,
          padding: c.padding,
          minHeight: c.minHeight,
          gap: c.gap,
          font: c.font,
          fontFamily: c.fontFamily,
          background: c.backgroundColor,
          border: c.border,
        };
      };
      return {
        body: describe(document.body),
        rows: [...document.querySelectorAll(".panel>.row")].slice(0, 3).map(describe),
        badges: [...document.querySelectorAll(".panel>.row:nth-child(2)>span")].map(describe),
        wrappers: [
          ...document.querySelectorAll(
            ".panel>.row:nth-child(2)>div,.panel>.row:nth-child(2)>div>div",
          ),
        ].map(describe),
      };
    });
    await page.screenshot({ path: `${output}/${mode}-projects.png` });
    await page.close();
  }
  fs.writeFileSync(`${output}/geometry.json`, JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
} finally {
  await browser.close();
  server.close();
}
