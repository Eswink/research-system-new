/**
 * Playwright 配置（PLAN-20260908-034 T31）。
 * 默认套件用确定性 API 替身（page.route 拦截 /api/*），不连真实后端、
 * 不使用付费 LLM 或真实凭据。live-*.spec.ts（api-workflow / artifact-diff /
 * experiment-queue / project-lineage）走 playwrightLive.config.ts（真实 FastAPI
 * + Fake Ports）。新增 live spec 时两处 testIgnore / testMatch 必须同步，否则
 * stub 套件会把真实链路一起收进来（无 live 服务 → 必然失败）。
 */

import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  testIgnore: /live-(api-workflow|artifact-diff|experiment-queue|project-lineage)\.spec\.ts/,
  timeout: 30_000,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"],
  },
  webServer: {
    command: "pnpm run dev --port 5173 --strictPort",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
