/**
 * e2e 共享确定性 API 替身（PLAN-20260908-033 AC-06）。
 *
 * page.route 拦截全部 /api 请求并返回固定数据：无真实后端、无付费 LLM、
 * 无凭据；页面渲染完全确定（截图基准依赖此确定性）。
 */

import type { Page, Route } from "@playwright/test";

export const VALID_YAML = [
  "id: sort_analysis_v1_0_1",
  "version: 0.4.0",
  "phases:",
  "  - id: execution",
  "    strategy: single_agent",
  "    required_roles:",
  "      - {role: experiment_engineer, min_instances: 1, max_instances: 1}",
  "    task_contract: sort_analysis_execution",
  "    timeout_seconds: 120",
].join("\n");

export const ENDPOINT = {
  id: "ep-1",
  name: "main",
  protocol: "OPENAI_COMPATIBLE",
  base_url: "https://relay.example",
  api_style: "chat_completions",
  enabled: true,
  credential: "configured",
  request_timeout_seconds: 30,
  max_retries: 3,
  concurrency_limit: 4,
  version: "1",
};

export const DRAFT = {
  draft_id: "pdraft_00000001",
  project_id: "example-project",
  name: "draft",
  revision: 1,
  yaml_text: VALID_YAML,
  source_digest: "sha256:aaaaaaaa",
  created_at: "2026-09-08T00:00:00Z",
  updated_at: "2026-09-08T00:00:00Z",
};

function fulfillJson(route: Route, body: unknown, status = 200): void {
  void route
    .fulfill({ status, contentType: "application/json", body: JSON.stringify(body) })
    .catch(() => undefined);
}

export async function stubApi(page: Page): Promise<void> {
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (!url.pathname.startsWith("/api/")) {
      void route.continue();
      return;
    }
    const path = url.pathname.replace(/^\/api/, "");
    const method = route.request().method();
    if (path === "/llm-endpoints" && method === "GET") {
      fulfillJson(route, [ENDPOINT]);
      return;
    }
    if (path === "/protocol-templates" && method === "GET") {
      fulfillJson(route, [
        {
          template_id: "sort-analysis",
          display_name: "Sort 分析（2-phase）",
          description: "执行 + 独立复核的参考场景",
          yaml_text: VALID_YAML,
          source: "examples/protocols/sort_analysis_v1.yaml",
        },
      ]);
      return;
    }
    if (path === "/projects/example-project/protocol-drafts" && method === "POST") {
      fulfillJson(route, DRAFT, 201);
      return;
    }
    fulfillJson(route, []);
  });
}
