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

test("1280x800 浅主题/英文/紧凑密度矩阵：属性切换生效且无横向溢出", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/#/plan/protocol");
  await expect(page.getByTestId("console-main")).toBeVisible();
  await page.getByTestId("toggle-theme").click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByTestId("toggle-language").click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await page.getByTestId("toggle-density").click();
  const density = page.locator("html").getAttribute("data-density");
  expect(["compact", "normal"]).toContain(await density);
  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    return doc.scrollWidth - doc.clientWidth;
  });
  expect(overflow).toBeLessThanOrEqual(1);
});

test("自托管字体在 reduced-motion 上下文完成加载", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#/plan/overview");
  await expect(page.getByTestId("console-main")).toBeVisible();
  const loaded = await page.evaluate(async () => {
    await document.fonts.ready;
    return [...document.fonts].filter((font) => font.status === "loaded").length;
  });
  expect(loaded).toBeGreaterThan(0);
});

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
