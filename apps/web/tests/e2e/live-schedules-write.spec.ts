/**
 * 真实 API live 链（PLAN-20260915-066 EC-03 / AC-05）：调度定义写面经真实 HTTP。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）；调度 store 与
 * registry 由 `tests/api/run_fixtures` 装配，守护线程在 lifespan 里注册执行体。
 * 由 playwrightLive.config.ts 驱动（vite /api 代理 → uvicorn:8011）。
 *
 * 定义名带时间戳：真实 SQLite 会跨轮次保留定义，同名会撞 409（本面不提供删除）。
 */

import { expect, test, type Page } from "@playwright/test";

const NAME = `live_relay_${Date.now().toString(36)}`;

interface ScheduleRow {
  name: string;
  job: string;
  interval_seconds: number;
  enabled: boolean;
  executor_attached: boolean;
  run_count: number;
  last_outcome: string | null;
}

async function row(page: Page): Promise<ScheduleRow | undefined> {
  const response = await page.request.get("/api/ops/schedules");
  const body = (await response.json()) as { schedules: ScheduleRow[] };
  return body.schedules.find((item) => item.name === NAME);
}

test("live: 登记 → 触发 → 停用（读面随写面变化）", async ({ page }) => {
  await page.goto("/#/ops/schedules", { waitUntil: "domcontentloaded" });
  await page.reload();
  await expect(page.getByTestId("schedules-panel")).toBeVisible();

  await page.getByTestId("schedule-name-input").fill(NAME);
  await page.getByTestId("schedule-job-select").selectOption("lease_recovery");
  await page.getByTestId("schedule-interval-input").fill("120");
  await page.getByTestId("schedule-create-submit").click();

  // 登记即生效：读面出现该定义，且带着"没有运行事实"的诚实初值
  await expect(page.getByTestId(`schedule-interval-${NAME}`)).toContainText("120");
  await expect(page.getByTestId(`schedule-facts-${NAME}`)).toContainText("UNKNOWN");
  expect((await row(page))?.executor_attached).toBe(true);

  // 触发：跑的是守护线程注册的同一条 pass，运行事实立刻 +1
  await page.getByTestId(`schedule-trigger-${NAME}`).click();
  await expect(page.getByTestId(`schedule-facts-${NAME}`)).toContainText("1 次");
  const ran = await row(page);
  expect(ran?.run_count).toBe(1);
  expect(ran?.last_outcome).toBe("OK");

  // 停用：写面翻转，触发按钮随之禁用
  await page.getByTestId(`schedule-toggle-${NAME}`).click();
  await expect(page.getByTestId(`schedule-enabled-${NAME}`)).toContainText("OFF");
  await expect(page.getByTestId(`schedule-trigger-${NAME}`)).toBeDisabled();
  expect((await row(page))?.enabled).toBe(false);

  // 停用不是"响应体自述"：服务端拒绝再次触发（409）
  const blocked = await page.request.post(`/api/ops/schedules/${NAME}/trigger`, {
    headers: { "Idempotency-Key": `live-066-blocked-${String(Date.now())}` },
  });
  expect(blocked.status()).toBe(409);

  // 复原：启用并改回小间隔，运行事实继续增长（定义变更下一轮生效）
  await page.getByTestId(`schedule-toggle-${NAME}`).click();
  await expect(page.getByTestId(`schedule-enabled-${NAME}`)).toContainText("ON");
  await page.getByTestId(`schedule-trigger-${NAME}`).click();
  await expect(page.getByTestId(`schedule-facts-${NAME}`)).toContainText("2 次");
});

test("live: 词表外作业与越界间隔被服务端拒绝", async ({ page }) => {
  await page.goto("/#/ops/schedules", { waitUntil: "domcontentloaded" });
  const headers = { "Idempotency-Key": `live-066-reject-${String(Date.now())}` };
  const unknownJob = await page.request.post("/api/ops/schedules", {
    headers,
    data: { name: `${NAME}_x`, job: "not_a_job", interval_seconds: 60 },
  });
  expect(unknownJob.status()).toBe(422);
  expect(await unknownJob.text()).toContain("worker_reaper");

  const badInterval = await page.request.post("/api/ops/schedules", {
    headers: { "Idempotency-Key": `live-066-reject2-${String(Date.now())}` },
    data: { name: `${NAME}_y`, job: "retention", interval_seconds: 0.5 },
  });
  expect(badInterval.status()).toBe(422);
});
