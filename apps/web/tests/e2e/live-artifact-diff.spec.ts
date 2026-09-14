/**
 * 真实 API live 链（PLAN-20260914-047 WP-D）：制品内容 diff 经真实 HTTP。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）；两份受控
 * 制品由该装配在启动时放入共享 store（见 console_api_app.LIVE_DIFF_ARTIFACTS）。
 * 由 playwrightLive.config.ts 驱动（vite /api 代理 → uvicorn:8011）。
 */

import { expect, test } from "@playwright/test";

const BEFORE = "live-fixture:before.json";
const AFTER = "live-fixture:after.json";

test("live: 制品 diff 返回行级变更", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const response = await page.request.get(`/api/artifacts/${BEFORE}/diff/${AFTER}`);
  expect(response.ok()).toBeTruthy();
  const body = (await response.json()) as {
    comparison: string;
    available: boolean;
    identical: boolean;
    stats: { added: number; removed: number; context: number };
    lines: { kind: string; text: string }[];
    note: string;
  };
  expect(body.comparison).toBe("ARTIFACT_CONTENT");
  expect(body.available).toBe(true);
  expect(body.identical).toBe(false);
  expect(body.stats).toEqual({ added: 1, removed: 1, context: 3 });
  const kinds = body.lines.map((line) => line.kind);
  expect(kinds).toContain("REMOVED");
  expect(kinds).toContain("ADDED");
  expect(body.lines.some((line) => line.text.includes('"status": "running"'))).toBe(true);
  expect(body.note).toContain("artifact content");
});

test("live: 同一制品自身比较为 identical，未知制品 404", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const self = await page.request.get(`/api/artifacts/${BEFORE}/diff/${BEFORE}`);
  expect(self.ok()).toBeTruthy();
  const body = (await self.json()) as { available: boolean; identical: boolean; lines: unknown[] };
  expect(body.available).toBe(true);
  expect(body.identical).toBe(true);
  expect(body.lines).toEqual([]);

  const ghost = await page.request.get("/api/artifacts/ghost-left/diff/ghost-right");
  expect(ghost.status()).toBe(404);
  const problem = (await ghost.json()) as { title: string };
  expect(problem.title).toBe("Artifact Not Found");
});
