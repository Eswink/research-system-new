/**
 * 真实 API live 链（PLAN-20260915-052 WP-D / G14）：实验队列经真实 HTTP。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）。
 * 覆盖：计划预注册 → 入队（协议来源立即解析）→ 队列视图 → 改期 → 取消；
 * 以及错误面（未知计划 404、非法来源 422）。派发器不在本链路上跑（真实 run
 * 启动由 tests/api/test_experiment_queue_api.py 用同一派发器验证）。
 */

import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

const PROTOCOL = "m12_reference_research_v1.yaml";
const PROJECT = "example-project";

interface PlanBody {
  id: string;
  name: string;
  state: string;
}

async function createPlan(page: Page, name: string): Promise<string> {
  const response = await page.request.post(`/api/projects/${PROJECT}/experiments`, {
    data: { name, hypothesis: "live queue chain" },
    headers: { "Idempotency-Key": `live-plan-${String(Date.now())}` },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  const plan = (await response.json()) as PlanBody;
  expect(plan.state).toBe("PREREGISTERED");
  return plan.id;
}

test("live: 入队 → 列表 → 改期 → 取消", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const planId = await createPlan(page, `live-queue-${String(Date.now())}`);

  const enqueued = await page.request.post(
    `/api/projects/${PROJECT}/experiments/${planId}/queue`,
    {
      data: { protocol_path: PROTOCOL },
      headers: { "Idempotency-Key": `live-enqueue-${String(Date.now())}` },
    },
  );
  expect(enqueued.status(), await enqueued.text()).toBe(201);
  const entry = (await enqueued.json()) as {
    id: string;
    state: string;
    plan_id: string;
    protocol_path: string | null;
  };
  expect(entry.state).toBe("QUEUED");
  expect(entry.plan_id).toBe(planId);
  expect(entry.protocol_path).toBe(PROTOCOL);

  const listed = await page.request.get(`/api/projects/${PROJECT}/experiment-queue`);
  expect(listed.ok()).toBeTruthy();
  const view = (await listed.json()) as { entries: { id: string }[]; dispatch_note: string };
  expect(view.entries.map((row) => row.id)).toContain(entry.id);

  const rescheduled = await page.request.patch(`/api/experiment-queue/${entry.id}`, {
    data: { not_before: "2030-01-01T00:00:00+00:00" },
    headers: { "Idempotency-Key": `live-resched-${String(Date.now())}` },
  });
  expect(rescheduled.ok(), await rescheduled.text()).toBeTruthy();
  const moved = (await rescheduled.json()) as { not_before: string | null; state: string };
  expect(moved.not_before).toContain("2030-01-01");
  expect(moved.state).toBe("QUEUED");

  const cancelled = await page.request.delete(`/api/experiment-queue/${entry.id}`, {
    headers: { "Idempotency-Key": `live-cancel-${String(Date.now())}` },
  });
  expect(cancelled.ok(), await cancelled.text()).toBeTruthy();
  expect(((await cancelled.json()) as { state: string }).state).toBe("CANCELLED");

  const again = await page.request.delete(`/api/experiment-queue/${entry.id}`, {
    headers: { "Idempotency-Key": `live-cancel-2-${String(Date.now())}` },
  });
  expect(again.status()).toBe(409);
});

test("live: 未知计划 404、来源二义 422", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const ghost = await page.request.post(`/api/projects/${PROJECT}/experiments/ghost/queue`, {
    data: { protocol_path: PROTOCOL },
    headers: { "Idempotency-Key": `live-ghost-${String(Date.now())}` },
  });
  expect(ghost.status()).toBe(404);

  const planId = await createPlan(page, `live-queue-bad-${String(Date.now())}`);
  const ambiguous = await page.request.post(
    `/api/projects/${PROJECT}/experiments/${planId}/queue`,
    {
      data: { protocol_path: PROTOCOL, draft_id: "draft-x", draft_revision: 1 },
      headers: { "Idempotency-Key": `live-amb-${String(Date.now())}` },
    },
  );
  expect(ambiguous.status()).toBe(422);
});
