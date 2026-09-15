/**
 * Console e2e（PLAN-20260915-055 WP-B / G9）：项目级来源血缘。
 *
 * 确定性 API 替身验证页面把后端合并图的三类事实如实呈现：
 * - 跨 Run 关系由**共享节点**表达（多个 run 贡献同一节点 ⇒ 标"（共享）"）；
 * - 库资源只出现在未连边清单（不猜测边）；
 * - 资源引用记录面的诚实说明原样输出，run 级仍如实声明全局血缘不在此端点提供。
 */

import { expect, test } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

const RUN_ID = "run-stub-1";

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test.afterEach(() => {
  assertNoUnmatched();
});

test("项目级血缘渲染共享节点、未连边库资源与诚实说明", async ({ page }) => {
  await page.goto(`/#/library/lineage?run=${RUN_ID}`);
  const panel = page.getByTestId("lineage-page");
  await expect(panel).toBeVisible();

  // 合并图摘要来自响应（2 run / 3 节点 / 1 边），不写死成装饰性数字。
  await expect(panel).toContainText("项目级合并图（运行 / 节点 / 边）：2 / 3 / 1");

  // 跨 run 关系只由共享节点表达：被两个 run 引用的来源标"（共享）"。
  const nodes = panel.getByRole("table", { name: "项目血缘节点" });
  await expect(nodes.getByRole("row").filter({ hasText: "paper://shared-2024" })).toContainText(
    "2（共享）",
  );

  // 未连边库资源清单：数据集与提示词只列不连。
  const resources = panel.getByRole("table", { name: "未连边库资源" });
  await expect(resources).toContainText("benchmark-v1");
  await expect(resources).toContainText("critic-v2");

  // 说明面：资源引用的记录边界必须如实出现（不画猜测的边）。
  await expect(panel).toContainText("无记录面");

  // run 级投影仍如实声明全局血缘不在此端点提供。
  await expect(panel).toContainText("项目级血缘见 GET /projects/{id}/lineage");
});
