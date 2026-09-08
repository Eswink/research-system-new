/**
 * 键盘可达性 + 屏宽验收（PLAN-20260908-034 T29/T31）。
 *
 * - Tab 遍历：前两停落在侧边导航（logo、首个域），焦点环可见；
 * - 模板面板：Esc 关闭后焦点恢复到触发按钮；
 * - 屏宽：1440/1280/1024/768/390 五档下代表路由无横向溢出。
 */

import { expect, test } from "@playwright/test";

import { stubApi } from "./stub-api";

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test("Tab 遍历：前几停可达侧边域导航且焦点环可见", async ({ page }) => {
  await page.goto("/#/plan/protocol");
  await page.getByTestId("console-main").waitFor({ state: "visible" });
  const seen: (string | undefined)[] = [];
  for (let i = 0; i < 4; i++) {
    await page.keyboard.press("Tab");
    seen.push(await page.evaluate(activeTestId));
  }
  expect(seen).toContain("nav-domain-plan");
  const shadow = await page.evaluate(() => {
    const el = document.activeElement;
    return el instanceof HTMLElement ? getComputedStyle(el).boxShadow : "";
  });
  expect(shadow).not.toBe("none");
});

test("模板面板：打开焦点入面板，Esc 关闭后焦点恢复到触发按钮", async ({ page }) => {
  await page.goto("/#/plan/protocol");
  await page.getByTestId("protocol-editor").waitFor({ state: "visible" });
  await page.getByTestId("templates-toggle").click();
  const picker = page.getByTestId("template-picker");
  await expect(picker).toBeVisible();
  const focusInPicker = await page.evaluate(pickerContainsActiveElement);
  expect(focusInPicker).toBe(true);
  await page.keyboard.press("Escape");
  await expect(picker).toHaveCount(0);
  const restored = await page.evaluate(activeElementId);
  expect(restored).toBe("templates-toggle");
});

const OVERFLOW_ROUTES = ["#/plan/protocol", "#/library/model-registry", "#/ops/observability"];

for (const width of [1440, 1280, 1024, 768, 390]) {
  for (const route of OVERFLOW_ROUTES) {
    test("无横向溢出 @" + String(width) + "px " + route, async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      await page.goto("/" + route);
      await expect(page.getByTestId("console-main")).toBeVisible();
      const overflow = await page.evaluate(() => {
        const doc = document.documentElement;
        return doc.scrollWidth - doc.clientWidth;
      });
      expect(overflow).toBeLessThanOrEqual(1);
    });
  }
}

function activeTestId(): string | undefined {
  return document.activeElement instanceof HTMLElement
    ? document.activeElement.dataset.testid
    : undefined;
}

function activeElementId(): string | undefined {
  return document.activeElement instanceof HTMLElement
    ? document.activeElement.id
    : undefined;
}

function pickerContainsActiveElement(): boolean {
  const host = document.querySelector("[data-testid='template-picker']");
  return host?.contains(document.activeElement) === true;
}
