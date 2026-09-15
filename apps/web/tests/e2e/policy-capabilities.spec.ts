/**
 * Console e2e（PLAN-20260914-049 WP-C）：策略面只读呈现。
 *
 * 验证 govern/audit → Memory Tab 渲染策略快照（policy id/version/默认判决 +
 * memory.write 逐 tier 有效判决）；策略收紧为 deny 时页面如实呈现 DENY 而非
 * 仍显示 ALLOW（不缓存假绿）。
 */

import { expect, test } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test.afterEach(() => {
  assertNoUnmatched();
});

test("策略面板呈现 policy 元数据与 memory.write 逐 tier 判决", async ({ page }) => {
  await page.goto("/#/govern/audit");
  await page.getByRole("tab", { name: "Memory" }).click();
  const panel = page.getByTestId("policy-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText("project-policy");
  await expect(panel).toContainText("0.4.0");
  await expect(panel).toContainText("DENY");
  const gate = page.getByTestId("gate-capability");
  await expect(gate).toContainText("memory.write");
  for (const tier of ["SESSION", "RUN", "PROJECT", "ORGANIZATION"]) {
    await expect(gate.getByRole("row", { name: new RegExp(tier) })).toContainText("ALLOW");
  }
});

test("策略收紧后页面如实呈现 DENY（不显示陈旧 ALLOW）", async ({ page }) => {
  await page.route("**/api/policy/capabilities", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        policy_id: "project-policy",
        version: "0.4.0",
        default_effect: "DENY",
        source: "examples/config/policy.yaml",
        rules: [],
        gate_capabilities: [
          {
            capability: "memory.write",
            scopes: ["PROJECT"],
            effects: { PROJECT: "DENY" },
            reasons: { PROJECT: "matched deny rule" },
          },
        ],
        note: "tightened for test",
      }),
    }),
  );
  await page.goto("/#/govern/audit");
  await page.getByRole("tab", { name: "Memory" }).click();
  const gate = page.getByTestId("gate-capability");
  const row = gate.getByRole("row", { name: /PROJECT/ });
  await expect(row).toContainText("DENY");
  await expect(row).toContainText("matched deny rule");
});
