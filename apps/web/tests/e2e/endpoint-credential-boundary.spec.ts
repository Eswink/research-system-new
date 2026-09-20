/**
 * 凭据边界读面（GOAL-20260920-008 EC-03 / PLAN-20260920-116 WP-E）。
 *
 * 为什么单独一条 spec：这条文案住在**端点详情抽屉**里，而设计对照路由
 * `library-endpoints` 的截图与结构签名都在**抽屉未打开**时取（`selected === undefined`
 * 时不渲染抽屉内容）——所以新文案对既有门禁完全不可见。这里显式打开抽屉，
 * 把两种语言下的边界声明钉在浏览器实跑上。
 *
 * 断言的是**事实声明**本身：值存在哪里（环境变量或进程内注册表）、重启后会怎样
 * （需重新注入），且**不得**出现任何「已托管保存」的说法。
 */

import { expect, test, type Page } from "@playwright/test";

import { stubApi } from "./stub-api";

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

async function openEndpointDrawer(page: Page): Promise<void> {
  await page.goto("/#/library/endpoints");
  await expect(page.getByTestId("endpoints-home")).toBeVisible();
  await page.getByTestId("endpoint-card").first().getByRole("button").click();
  await expect(page.getByTestId("endpoint-credential-boundary")).toBeVisible();
}

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test("中文读面：说明凭据只在本进程/环境变量里，重启后需重新注入", async ({ page }) => {
  await seedLanguage(page, "zh");
  await openEndpointDrawer(page);
  const notice = page.getByTestId("endpoint-credential-boundary");
  await expect(notice).toContainText("只存在于环境变量或进程内注册表");
  await expect(notice).toContainText("重启后需重新注入");
  await expect(notice).toContainText("不是 Secret Manager");
});

test("英文读面：同一条边界，不得暗示已托管保存", async ({ page }) => {
  await seedLanguage(page, "en");
  await openEndpointDrawer(page);
  const notice = page.getByTestId("endpoint-credential-boundary");
  await expect(notice).toContainText("environment variables or the in-process registry");
  await expect(notice).toContainText("re-enter after restart");
  await expect(notice).toContainText("not a Secret Manager");
  // 反向断言：读面不得出现任何「已保存到托管存储」的说法。
  await expect(notice).not.toContainText("Secret Store");
  await expect(notice).not.toContainText("saved");
});
