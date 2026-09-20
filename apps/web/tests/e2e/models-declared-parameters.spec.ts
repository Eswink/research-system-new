/**
 * 声明参数读面（GOAL-20260920-008 EC-02 / PLAN-20260920-115 WP-E）。
 *
 * 为什么单独一条 spec：默认替身没注册 `GET /models`，设计对照路由
 * `library-model-registry` 因此渲染的是错误态——声明参数的新渲染分支在既有
 * 门禁上**不可见**（与 GOAL-007 EC-04 "加行后结构签名不变"同因）。这里显式
 * 提供两个模型（有声明 / 无声明），把两种态都钉在浏览器实跑上。
 *
 * 断言的是**文案事实**而不只是 DOM 存在：声明值必须与"声明不等于已生效"
 * 的说明同屏出现，无声明必须渲染为"未声明"而不是某个默认值。
 */

import { expect, test, type Page } from "@playwright/test";

import { stubApi } from "./stub-api";

const DECLARED = {
  id: "model-declared",
  endpoint_id: "endpoint-one",
  model_name: "agnes-2.5-flash",
  display_name: "Declared model",
  enabled: true,
  capabilities: {},
  context_window_tokens: 512000,
  thinking_intensity: "MAX",
  version: "sha256:declared",
};

const UNDECLARED = {
  id: "model-undeclared",
  endpoint_id: "endpoint-one",
  model_name: "plain-model",
  display_name: "Undeclared model",
  enabled: true,
  capabilities: {},
  context_window_tokens: null,
  thinking_intensity: null,
  version: "sha256:undeclared",
};

/** 显式选语言：诚实文案是本地化字符串，断言必须先钉住渲染语言。 */
async function seedLanguage(page: Page, language: "en" | "zh"): Promise<void> {
  await page.addInitScript((lang) => {
    localStorage.setItem(
      "ros.console.preferences",
      JSON.stringify({
        theme: "dark",
        density: "normal",
        language: lang,
        editorMode: "form",
        version: "test",
      }),
    );
  }, language);
}

test.beforeEach(async ({ page }) => {
  await stubApi(page);
  await page.route("**/api/models", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([DECLARED, UNDECLARED]),
    }),
  );
  await page.route("**/api/models/*/compatibility", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        model: DECLARED,
        endpoint_id: DECLARED.endpoint_id,
        endpoint_healthy_hint: null,
        hard_capability_requirements: [],
      }),
    }),
  );
  await page.route("**/api/models/model-declared", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(DECLARED),
    }),
  );
});

test("有声明：表列与详情都渲染声明值，并写明声明不等于已生效", async ({ page }) => {
  await seedLanguage(page, "en");
  await page.goto("/#/library/model-registry");
  await expect(page.getByTestId("models-page")).toBeVisible();
  await expect(page.getByTestId("models-page")).toContainText("agnes-2.5-flash");

  const row = page.getByRole("row", { name: /agnes-2\.5-flash/ });
  await expect(row.getByTestId("model-row-declared")).toContainText("512000 tok");
  await expect(row.getByTestId("model-row-declared")).toContainText("MAX");

  const details = page.getByTestId("model-declared-parameters");
  await expect(details).toContainText("512000 tokens");
  await expect(details).toContainText("MAX");
  // 诚实文案：声明值不发送给 provider、不参与 eligibility。
  await expect(details).toContainText("not sent to the provider");
});

test("有声明：中文读面同样写明声明不等于已生效", async ({ page }) => {
  await seedLanguage(page, "zh");
  await page.goto("/#/library/model-registry");
  const details = page.getByTestId("model-declared-parameters");
  await expect(details).toContainText("512000 tokens");
  await expect(details).toContainText("不发送给 provider");
});

test("无声明：渲染为未声明，不推断默认值", async ({ page }) => {
  await seedLanguage(page, "en");
  await page.goto("/#/library/model-registry");
  await expect(page.getByTestId("models-page")).toBeVisible();
  const row = page.getByRole("row", { name: /plain-model/ });
  await expect(row.getByTestId("model-row-declared")).toHaveText("—");
  // 选中无声明模型时详情必须说「未声明」，不得显示某个默认窗口/强度。
  await row.click();
  const details = page.getByTestId("model-declared-parameters");
  await expect(details).toContainText("not declared");
  await expect(details).toContainText("undeclared does not mean a default is applied");
});
