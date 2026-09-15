/**
 * Playwright 配置（PLAN-20260908-034 T31）。
 * 默认套件用确定性 API 替身（page.route 拦截 /api/*），不连真实后端、
 * 不使用付费 LLM 或真实凭据。live-*.spec.ts 走 playwrightLive.config.ts
 * （真实 FastAPI + Fake Ports）；两份配置共用 tests/e2e/live-specs.ts 的
 * LIVE_SPEC_PATTERN（单一来源；新增 live spec 只改那里）。
 */

import { defineConfig, devices } from "@playwright/test";

import { LIVE_SPEC_PATTERN } from "./tests/e2e/live-specs";

export default defineConfig({
  testDir: "./tests/e2e",
  testIgnore: LIVE_SPEC_PATTERN,
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
