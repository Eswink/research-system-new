/**
 * Console e2e（PLAN-20260915-066 EC-03）：调度定义写面。
 *
 * 核心口径：**写面被读面消费**。登记后行出现且带着"没有运行事实"的诚实初值；
 * 触发后同一行的运行事实变化（这就是 pass 真的跑过的证据）；停用后启用位翻转、
 * 触发按钮禁用（无执行体的作业同样禁用并说明原因）。
 */

import { expect, test, type Page } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";
import { resetScheduleStub } from "./stub-routes-schedules";

test.beforeEach(() => {
  resetScheduleStub();
});

test.afterEach(() => {
  assertNoUnmatched();
});

async function openSchedules(page: Page): Promise<void> {
  await stubApi(page);
  await page.goto("/#/ops/schedules");
  await expect(page.getByTestId("schedules-page")).toBeVisible();
  await expect(page.getByTestId("schedules-panel")).toBeVisible();
}

async function createSchedule(page: Page, name: string, interval: string): Promise<void> {
  await page.getByTestId("schedule-name-input").fill(name);
  await page.getByTestId("schedule-interval-input").fill(interval);
  await page.getByTestId("schedule-create-submit").click();
}

test("登记：新定义出现在表里，运行事实诚实为「未运行」", async ({ page }) => {
  await openSchedules(page);
  await createSchedule(page, "outbox_relay_fast", "45");

  await expect(page.getByTestId("schedule-interval-outbox_relay_fast")).toContainText("45");
  await expect(page.getByTestId("schedule-facts-outbox_relay_fast")).toContainText("0 次");
  await expect(page.getByTestId("schedule-facts-outbox_relay_fast")).toContainText("UNKNOWN");
  await expect(page.getByTestId("schedules-note")).toContainText("执行体仍是进程内守护线程");
});

test("触发：运行事实在读到的那一行上变化（写面被读面消费）", async ({ page }) => {
  await openSchedules(page);
  await expect(page.getByTestId("schedule-facts-lease_recovery")).toContainText("0 次");

  await page.getByTestId("schedule-trigger-lease_recovery").click();

  await expect(page.getByTestId("schedule-facts-lease_recovery")).toContainText("1 次");
  await expect(page.getByTestId("schedule-facts-lease_recovery")).toContainText("OK");
});

test("启停：停用后启用位翻转，且触发按钮禁用", async ({ page }) => {
  await openSchedules(page);
  await page.getByTestId("schedule-toggle-lease_recovery").click();

  await expect(page.getByTestId("schedule-enabled-lease_recovery")).toContainText("OFF");
  await expect(page.getByTestId("schedule-trigger-lease_recovery")).toBeDisabled();

  await page.getByTestId("schedule-toggle-lease_recovery").click();
  await expect(page.getByTestId("schedule-enabled-lease_recovery")).toContainText("ON");
  await expect(page.getByTestId("schedule-trigger-lease_recovery")).toBeEnabled();
});

test("无执行体的作业：如实标注且不能触发", async ({ page }) => {
  await openSchedules(page);
  await expect(page.getByTestId("schedule-executor-retention")).toContainText("无执行体");
  await expect(page.getByTestId("schedule-trigger-retention")).toBeDisabled();
  await expect(page.getByTestId("schedule-executor-lease_recovery")).toContainText("已连接");
});

test("服务端拒绝（重名 409）落在面板内，不是静默失败", async ({ page }) => {
  await openSchedules(page);
  await createSchedule(page, "lease_recovery", "60");
  await expect(page.getByTestId("schedule-create-error")).toContainText("already exists");
});
