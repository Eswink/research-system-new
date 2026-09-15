/**
 * 真实 FastAPI HTTP 集成（PLAN-20260915-057 WP-B / G12 项目级成本预测）。
 *
 * 后端为 tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）。验证真实装配面上
 * `GET /projects/{id}/cost-forecast` 的口径：方法/样本/排除随响应返回、horizon 越界 422、
 * 幽灵项目空序列（NO_VALUED_DAYS）而不是 404、预算口径指向 run 级端点。
 */

import { expect, test } from "@playwright/test";

test("live: 项目级成本预测口径与边界", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const response = await page.request.get("/api/projects/example-project/cost-forecast");
  expect(response.ok()).toBeTruthy();
  const view = (await response.json()) as {
    project_id: string;
    days: { date: string; included_in_projection: boolean; exclusion_reason: string | null }[];
    projection: {
      method: string;
      horizon_days: number;
      valued_days: number;
      excluded_days: number;
      unavailable_reason: string | null;
      projected_minor: number | null;
      note: string;
    };
    unattributed_entries: number;
    scope_note: string;
  };
  expect(view.project_id).toBe("example-project");
  expect(view.projection.method).toBe("MEAN_OF_VALUED_DAYS");
  expect(view.projection.horizon_days).toBe(7);
  expect(view.projection.note).toContain("not a commitment");
  expect(view.scope_note).toContain("reserved-vs-consumed");
  // 日序列只含真实存在的数据日：被排除的那天必须给出原因（不静默丢天）。
  for (const day of view.days) {
    if (!day.included_in_projection) expect(day.exclusion_reason).not.toBeNull();
  }
  expect(view.projection.valued_days + view.projection.excluded_days).toBe(view.days.length);

  // 视野越界 422；自定义视野被如实回显。
  const outOfRange = await page.request.get(
    "/api/projects/example-project/cost-forecast?horizon_days=0",
  );
  expect(outOfRange.status()).toBe(422);
  const horizon = await page.request.get(
    "/api/projects/example-project/cost-forecast?horizon_days=30",
  );
  const horizonView = (await horizon.json()) as { projection: { horizon_days: number } };
  expect(horizonView.projection.horizon_days).toBe(30);

  // 幽灵项目：空序列 + NO_VALUED_DAYS（与 /projects/{id}/runs 同口径，不 404）。
  const ghost = await page.request.get("/api/projects/ghost-project/cost-forecast");
  expect(ghost.status()).toBe(200);
  const empty = (await ghost.json()) as {
    days: unknown[];
    projection: { valued_days: number; projected_minor: number | null; unavailable_reason: string };
  };
  expect(empty.days).toEqual([]);
  expect(empty.projection.valued_days).toBe(0);
  expect(empty.projection.projected_minor).toBeNull();
  expect(empty.projection.unavailable_reason.startsWith("NO_VALUED_DAYS")).toBe(true);
});
