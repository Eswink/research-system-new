/**
 * 示例模式浏览器实跑（PLAN-20260909-035 WP4.2）。
 *
 * 33 条规范路由在 `?source=example` 下逐一渲染：监听全部 /api 请求与 pageerror，
 * 断言示例页零业务 API 调用；再对关键示例交互（搜索过滤、详情抽屉、预检确认门）
 * 做真实操作验证，操作后仍不得出现任何业务请求。
 */

import { expect, test, type Page } from "@playwright/test";

import { CANONICAL_ROUTES } from "../../src/navigation/registry";

function exampleTestId(domain: string, page: string): string {
  return `example-page-${domain}-${page}`;
}

function watchApi(page: Page): string[] {
  const apiCalls: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.startsWith("/api")) {
      apiCalls.push(`${request.method()} ${new URL(request.url()).pathname}`);
    }
  });
  return apiCalls;
}

function watchErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("pageerror", (error) => {
    errors.push(error.message);
  });
  return errors;
}

test("33 条路由 example 模式渲染且零业务 API 请求、零 pageerror", async ({ page }) => {
  test.setTimeout(240_000);
  for (const route of CANONICAL_ROUTES) {
    const apiCalls = watchApi(page);
    const pageErrors = watchErrors(page);
    await page.goto(`/?source=example#/${route.domain}/${route.page}`);
    await expect(page.getByTestId(exampleTestId(route.domain, route.page))).toBeVisible({
      timeout: 15_000,
    });
    await expect.poll(() => apiCalls.length, { timeout: 2_000 }).toBe(0);
    expect(pageErrors, `${route.domain}/${route.page} pageerror`).toEqual([]);
  }
});

test("示例项目页：搜索过滤与详情抽屉真实工作且不发业务请求", async ({ page }) => {
  const apiCalls = watchApi(page);
  watchErrors(page);
  await page.goto("/?source=example#/portfolio/projects");
  const surface = page.locator('[data-design-surface="example"]');
  await expect(surface.getByText("Multilingual Medical QA Hallucination")).toBeVisible();
  await surface.locator("input").first().fill("RAG");
  await expect(surface.getByText("Multilingual Medical QA Hallucination")).toBeHidden();
  await expect(surface.getByText("RAG Grounding Failure Modes")).toBeVisible();
  expect(apiCalls).toEqual([]);
  await surface.locator("input").first().fill("");
  await surface.getByText("Multilingual Medical QA Hallucination").first().click();
  const drawer = page.getByRole("dialog");
  await expect(drawer).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  expect(apiCalls).toEqual([]);
});

test("示例协议页：预检警告确认门控制启动按钮且不发业务请求", async ({ page }) => {
  const apiCalls = watchApi(page);
  watchErrors(page);
  await page.goto("/?source=example#/plan/protocol");
  const surface = page.locator('[data-design-surface="example"]');
  await expect(surface).toBeVisible();
  const ack = surface.locator('input[type="checkbox"]');
  await expect(ack).toBeVisible();
  const start = page.getByRole("button", { name: /启动运行|Start Run/ });
  await expect(start).toBeDisabled();
  await ack.check();
  await expect(start).toBeEnabled();
  await start.click();
  await expect(page.getByTestId("example-start-note")).toBeVisible();
  expect(apiCalls).toEqual([]);
});
