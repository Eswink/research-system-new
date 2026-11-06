/**
 * 程序页三件（GOAL-20261107-107 EC-02）。
 *
 * **它补哪三格**（此前都是「后端做完了、页面上零显示」）：
 *
 * ① **建程序表单** —— `POST /projects/{id}/programs` 此前只有 `programsClient.create`
 *    字面量，连 `client.ts` 都没导出 ⇒ 零调用点；
 * ② **逐轮决定时间线** —— `GET /programs/{id}` 早就返回 `decisions[]`（`after_index` /
 *    `kind` / `reason` / `decided_at`），页面上一个字都没有；
 * ③ **`cited_facts` 逐条可展开** —— 决定「为何继续 / 为何停」的原文依据。
 *
 * 三条判据（第二、三条是反证臂）：
 * ① 有决定的程序 ⇒ 时间线逐条渲染，展开后 `cited_facts` 逐条可见；
 * ② 没有决定的程序 ⇒ **明确空态**，不伪造一行；
 * ③ 表单提交 ⇒ 真的发出 POST（不是只换个文案）。
 */

import { expect, test } from "@playwright/test";

import { stubApi } from "./stub-api";

test("有决定的程序把逐轮决定与 cited_facts 渲染出来", async ({ page }) => {
  await stubApi(page);
  await page.goto("/#/portfolio/projects");
  const row = page.getByTestId("program-row-program-2");
  await expect(row).toBeVisible({ timeout: 8_000 });

  // ① 两条决定各一行，种类与序号都来自服务端。
  await expect(page.getByTestId("program-decision-0")).toContainText("CONTINUE");
  await expect(page.getByTestId("program-decision-1")).toContainText("STOP");

  // ② `cited_facts` 默认收起，点开后逐条可见（该行有 2 条事实）。
  const toggle = page.getByTestId("program-cited-toggle-1");
  await expect(page.getByTestId("program-cited-1")).toHaveCount(0);
  await toggle.click();
  const facts = page.getByTestId("program-cited-1");
  await expect(facts).toBeVisible();
  await expect(facts).toContainText("verdict=REJECT");
});

test("没有决定的程序显示空态，不伪造一行", async ({ page }) => {
  await stubApi(page);
  await page.goto("/#/portfolio/projects");
  const row = page.getByTestId("program-row-program-1");
  await expect(row).toBeVisible({ timeout: 8_000 });
  // 空态在场，且**没有**任何 `program-decision-*` 行（伪造会被这一条抓住）。
  await expect(page.getByTestId("program-timeline-empty-program-1")).toBeVisible();
  await expect(row.locator('[data-testid^="program-decision-"]')).toHaveCount(0);
});

test("建程序表单真的发出 POST 并显示服务端返回的 id", async ({ page }) => {
  await stubApi(page);
  const posted: string[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().includes("/programs")) {
      posted.push(request.url());
    }
  });
  await page.goto("/#/portfolio/projects");
  const form = page.getByTestId("program-create-form");
  await expect(form).toBeVisible({ timeout: 8_000 });

  await form.getByLabel("协议路径").fill("examples/protocols/direction_to_manuscript_v1.yaml");
  await page.getByTestId("program-create-submit").click();

  // ③ 发出去了，且结果来自服务端（`program-1` 是 stub 的返回值，不是前端编的）。
  await expect(page.getByTestId("program-create-result")).toContainText("program-1");
  expect(posted.length).toBe(1);
});
