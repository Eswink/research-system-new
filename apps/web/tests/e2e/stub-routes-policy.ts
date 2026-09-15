/**
 * 策略面 API 替身路由（PLAN-20260914-049 WP-C）。
 *
 * 形状遵循真实 DTO（services/api/dto/policy.py）：声明规则 + 门链能力逐 scope
 * 有效判决。默认全 tier ALLOW，与 examples/config/policy.yaml 的现状一致；
 * 需要验证"策略收紧后页面如实呈现"时在测试内覆盖该路由（page.route）。
 */

import type { StubRoute } from "./stub-routes";

const TIERS = ["ORGANIZATION", "PROJECT", "RUN", "SESSION"] as const;

export const POLICY_ROUTES: readonly StubRoute[] = [
  {
    method: "GET",
    pattern: /^\/policy\/capabilities$/,
    handler: () => ({
      status: 200,
      body: {
        policy_id: "project-policy",
        version: "0.4.0",
        default_effect: "DENY",
        source: "examples/config/policy.yaml",
        rules: [
          {
            effect: "ALLOW",
            capability: "memory.write",
            action: null,
            scope: "SESSION",
            constraints: {},
          },
        ],
        gate_capabilities: [
          {
            capability: "memory.write",
            scopes: [...TIERS],
            effects: Object.fromEntries(TIERS.map((tier) => [tier, "ALLOW"])),
            reasons: Object.fromEntries(TIERS.map((tier) => [tier, "matched allow rule"])),
          },
        ],
        note: "stub policy snapshot",
      },
    }),
  },
];
