/**
 * 真实链路（live-*.spec.ts）用例清单的**单一来源**（PLAN-20260915-057 WP-B）。
 *
 * `playwright.config.ts`（stub 套件）用它做 `testIgnore`，`playwrightLive.config.ts`
 * 用它做 `testMatch`：两份配置必须一致，否则 stub 套件会把真实链路一起收进来
 * （无 live 服务 → 必然失败）。新增 live spec 时只在这里加一项。
 */

const LIVE_SUITES = [
  "api-workflow",
  "artifact-diff",
  "experiment-queue",
  "project-lineage",
  "project-cost-forecast",
  "project-registry",
  "workspace-snapshots",
  "ops-write",
  "registry-write",
];

/** 匹配 `live-<suite>.spec.ts`（仅文件名，不含目录）。 */
export const LIVE_SPEC_PATTERN = new RegExp(`live-(${LIVE_SUITES.join("|")})\\.spec\\.ts`);
