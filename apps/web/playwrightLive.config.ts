/**
 * 真实 API 浏览器集成测试配置（PLAN-20260908-034 T30/T31）。
 *
 * 启动 tests/api/console_api_app（uvicorn:8011，Fake Ports）+ vite dev（:5174，
 * /api 代理到 8011）。仅运行 live-*.spec.ts。端口受控、不复用运行进程。
 */

import { defineConfig, devices } from "@playwright/test";

const API_PORT = 8011;
const WEB_PORT = 5174;

export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: /live-(api-workflow|artifact-diff)\.spec\.ts/,
  timeout: 60_000,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${String(WEB_PORT)}`,
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"],
  },
  webServer: [
    {
      command:
        `uv run --frozen --no-sync python -m uvicorn tests.api.console_api_app:app ` +
        `--host 127.0.0.1 --port ${String(API_PORT)}`,
      cwd: "../..",
      url: `http://127.0.0.1:${String(API_PORT)}/protocol-templates`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `pnpm run dev --host 127.0.0.1 --port ${String(WEB_PORT)} --strictPort`,
      url: `http://127.0.0.1:${String(WEB_PORT)}`,
      reuseExistingServer: false,
      timeout: 60_000,
      env: { RESEARCHOS_API_PROXY_TARGET: `http://127.0.0.1:${String(API_PORT)}` },
    },
  ],
});
