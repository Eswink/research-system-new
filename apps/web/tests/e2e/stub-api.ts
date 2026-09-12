/**
 * e2e 严格 API 替身（PLAN-20260908-034 T10）。
 *
 * 替换旧空数组兜底：未注册的 /api 请求立即使测试失败（route.abort + 记录违规），
 * 已支持 API 的样例遵循真实 DTO 形状。无后端页面的填充数据只进入隔离的视觉
 * 测试组合入口（见 visualFixtures），不加入生产路由/生产 API 客户端。
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

type Handler = (url: URL, body: unknown) => { status: number; body: unknown };

/** 收集未匹配请求，测试结束断言为空。 */
export const unmatchedRequests: string[] = [];

const ROUTES: readonly { method: string; pattern: RegExp; handler: Handler }[] = [
  {
    method: "GET",
    pattern: /^\/llm-endpoints$/,
    handler: () => ({ status: 200, body: [ENDPOINT] }),
  },
  {
    method: "GET",
    pattern: /^\/llm-endpoints\/[^/]+$/,
    handler: () => ({ status: 200, body: ENDPOINT }),
  },
  {
    method: "PATCH",
    pattern: /^\/llm-endpoints\/[^/]+$/,
    handler: () => ({ status: 200, body: ENDPOINT }),
  },
  {
    method: "POST",
    pattern: /^\/llm-endpoints\/[^/]+\/test$/,
    handler: () => ({
      status: 200,
      body: {
        ok: false,
        returned_model_name: null,
        system_fingerprint: null,
        error_category: "MODEL_UNAVAILABLE",
        error_message_redacted: null,
        probed_at: "2026-09-10T00:00:00Z",
      },
    }),
  },
  {
    method: "GET",
    pattern: /^\/protocol-templates$/,
    handler: () => ({
      status: 200,
      body: [
        {
          template_id: "sort-analysis",
          display_name: "Sort 分析（2-phase）",
          description: "执行 + 独立复核的参考场景",
          yaml_text: VALID_YAML,
          source: "examples/protocols/sort_analysis_v1.yaml",
        },
      ],
    }),
  },
  {
    method: "GET",
    pattern: /^\/protocol-drafts\/[^/]+$/,
    handler: () => ({ status: 200, body: DRAFT }),
  },
  {
    method: "POST",
    pattern: /^\/projects\/example-project\/protocol-drafts$/,
    handler: () => ({ status: 201, body: DRAFT }),
  },
  {
    method: "GET",
    pattern: /^\/projects\/example-project\/protocol-drafts$/,
    handler: () => ({ status: 200, body: [] }),
  },
  {
    method: "GET",
    pattern: /^\/projects\/example-project\/runs$/,
    handler: () => ({ status: 200, body: [] }),
  },
  {
    method: "GET",
    pattern: /^\/cluster\/workers$/,
    handler: () => ({ status: 200, body: { workers: [] } }),
  },
  {
    method: "GET",
    pattern: /^\/roles$|^\/team-templates$/,
    handler: () => ({ status: 200, body: [] }),
  },
  {
    method: "GET",
    pattern: /^\/projects\/example-project\/agents$/,
    handler: () => ({ status: 200, body: [] }),
  },
  {
    method: "GET",
    pattern: /^\/projects\/example-project\/settings$/,
    handler: () => ({
      status: 200,
      body: {
        project_id: "example-project",
        team_template_id: "standard",
        default_model_profile_id: null,
        budget_policy_id: "low_cost",
        workspace_backend: "openhands_docker",
        compute_profile: null,
        policy_id: "project-policy",
        reference_protocol: "ai_ml_research_v0_4_0.yaml",
      },
    }),
  },
  {
    method: "GET",
    pattern: /^\/approvals$/,
    handler: () => ({ status: 200, body: [] }),
  },
  {
    method: "GET",
    pattern: /^\/cost\/daily$/,
    handler: () => ({
      status: 200,
      body: { truncated: false, days: [], attribution_note: null },
    }),
  },
  {
    method: "GET",
    pattern: /^\/projects\/example-project\/experiments$/,
    handler: () => ({
      status: 200,
      body: { experiments: [], reproduction_note: "stub fixture" },
    }),
  },
  {
    method: "GET",
    pattern: /^\/notifications$/,
    handler: () => ({
      status: 200,
      body: {
        notifications: [
          {
            id: "evt-notify-1",
            type: "manifest.frozen",
            run_id: "run-notify-1",
            task_id: null,
            occurred_at: "2026-09-10T00:00:00Z",
            read: false,
          },
        ],
        note: "stub projection",
      },
    }),
  },
  {
    method: "GET",
    pattern: /^\/projects\/example-project\/memory$/,
    handler: () => ({
      status: 503,
      body: {
        type: "about:blank",
        title: "Memory Store Unavailable",
        status: 503,
        detail: "memory store requires the PostgreSQL control plane",
        instance: "/memory",
      },
    }),
  },
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/artifacts$/,
    handler: () => ({
      status: 503,
      body: {
        type: "about:blank",
        title: "Artifact Store Unavailable",
        status: 503,
        detail: "artifact store not configured",
        instance: "/artifacts",
      },
    }),
  },
  {
    method: "POST",
    pattern: /^\/memory\/proposals$/,
    handler: () => ({
      status: 503,
      body: {
        type: "about:blank",
        title: "Memory Store Unavailable",
        status: 503,
        detail: "memory store requires the PostgreSQL control plane",
        instance: "/memory/proposals",
      },
    }),
  },
  {
    method: "POST",
    pattern: /^\/notifications\/[^/]+\/read$/,
    handler: () => ({ status: 204, body: null }),
  },
  {
    method: "POST",
    pattern: /^\/projects\/example-project\/experiments$/,
    handler: () => ({
      status: 503,
      body: {
        type: "about:blank",
        title: "Experiment Store Unavailable",
        status: 503,
        detail: "experiment store requires the PostgreSQL control plane",
        instance: "/projects/example-project/experiments",
      },
    }),
  },
  // WP-B/WP-C control-plane surface: run approval history, DELETE (G10),
  // custom contracts and agent clone. Registered so interaction specs never hit
  // the "Unstubbed Request" failure; responses are honest empty/success shapes.
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/approvals$/,
    handler: () => ({ status: 200, body: [] }),
  },
  {
    method: "DELETE",
    pattern: /^\/llm-endpoints\/[^/]+$/,
    handler: () => ({ status: 204, body: null }),
  },
  {
    method: "DELETE",
    pattern: /^\/models\/[^/]+$/,
    handler: () => ({ status: 204, body: null }),
  },
  {
    method: "DELETE",
    pattern: /^\/protocol-drafts\/[^/]+$/,
    handler: () => ({ status: 204, body: null }),
  },
  {
    method: "DELETE",
    pattern: /^\/agents\/[^/]+$/,
    handler: () => ({ status: 204, body: null }),
  },
];

function match(path: string, method: string): Handler | null {
  for (const route of ROUTES) {
    if (route.method === method && route.pattern.test(path)) {
      return route.handler;
    }
  }
  return null;
}

function fulfill(route: Route, status: number, body: unknown): void {
  void route
    .fulfill({ status, contentType: "application/json", body: JSON.stringify(body) })
    .catch(() => undefined);
}

export async function stubApi(page: Page): Promise<void> {
  unmatchedRequests.length = 0;
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (!url.pathname.startsWith("/api/")) {
      void route.continue();
      return;
    }
    const path = url.pathname.replace(/^\/api/, "");
    const method = route.request().method();
    const handler = match(path, method);
    if (handler === null) {
      unmatchedRequests.push(`${method} ${url.pathname}`);
      fulfill(route, 500, {
        type: "about:blank",
        title: "Unstubbed Request",
        status: 500,
        detail: `No stub for ${method} ${path}`,
        instance: path,
      });
      return;
    }
    const post = route.request().postData();
    let body: unknown;
    try {
      body = post ? JSON.parse(post) : undefined;
    } catch {
      body = undefined;
    }
    const result = handler(url, body);
    fulfill(route, result.status, result.body);
  });
}

/** 测试内断言：无未匹配请求。 */
export function assertNoUnmatched(): void {
  if (unmatchedRequests.length > 0) {
    const list = unmatchedRequests.join(", ");
    unmatchedRequests.length = 0;
    throw new Error(`Unstubbed API requests: ${list}`);
  }
}
