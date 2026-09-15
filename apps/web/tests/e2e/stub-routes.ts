/**
 * e2e 严格 API 替身的样例数据与路由表（PLAN-20260908-034 T10；从 stub-api.ts
 * 拆出以守 450 行硬上限）。形状遵循真实 DTO；无后端页面的填充数据只进入隔离
 * 视觉测试组合入口（见 visualFixtures），不加入生产路由/生产 API 客户端。
 */

import { BUDGET_ROUTES } from "./stub-routes-budget";
import { EXPERIMENT_QUEUE_ROUTES } from "./stub-routes-experiments";
import { LINEAGE_ROUTES } from "./stub-routes-lineage";
import { OPS_ROUTES } from "./stub-routes-ops";
import { POLICY_ROUTES } from "./stub-routes-policy";
import { REGISTRY_ROUTES } from "./stub-routes-registry";
import { WORKSPACE_ROUTES } from "./stub-routes-workspace";
import { DRAFT, ENDPOINT, VALID_YAML } from "./stub-fixtures";

export type { Handler } from "./stub-fixtures";
export { DRAFT, ENDPOINT, VALID_YAML } from "./stub-fixtures";

export interface StubRoute {
  method: string;
  pattern: RegExp;
  handler: (url: URL, body: unknown) => { status: number; body: unknown };
}

export const ROUTES: readonly StubRoute[] = [
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
    pattern: /^\/projects$/,
    handler: () => ({
      status: 200,
      body: [
        {
          id: "example-project",
          name: "Example ML Research",
          status: "ACTIVE",
          created_at: "1970-01-01T00:00:00+00:00",
          updated_at: "1970-01-01T00:00:00+00:00",
        },
      ],
    }),
  },
  {
    method: "POST",
    pattern: /^\/projects$/,
    handler: (_url, body) => ({
      status: 201,
      body: {
        id: "proj-stubbed-1",
        name: (body as { name?: string }).name ?? "stub project",
        status: "ACTIVE",
        created_at: "2026-09-13T00:00:00+00:00",
        updated_at: "2026-09-13T00:00:00+00:00",
      },
    }),
  },
  {
    method: "PATCH",
    pattern: /^\/projects\/[^/]+$/,
    handler: (url, body) => ({
      status: 200,
      body: {
        id: decodeURIComponent(url.pathname.split("/").pop() ?? ""),
        name: (body as { name?: string }).name ?? "Example ML Research",
        status: (body as { status?: string }).status ?? "ACTIVE",
        created_at: "1970-01-01T00:00:00+00:00",
        updated_at: "2026-09-13T00:00:00+00:00",
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
  // PLAN-043 EC-02: run deliverable and run lineage
  // (honest empty/shape responses; interaction specs assert real rendering).
  // PLAN-060：/tool-providers 目录改由 stub-routes-registry 提供（要随注册状态变化）。
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/deliverable$/,
    handler: (url) => ({
      status: 200,
      body: {
        run_id: url.pathname.split("/")[2] ?? "",
        available: false,
        reason: "no persisted deliverable for this run",
        artifact_id: null,
        artifact_digest: null,
        deliverable: {},
      },
    }),
  },
  // PLAN-044 EC-03: library catalog (prompts/datasets/notebooks) read + create.
  {
    method: "GET",
    pattern: /^\/projects\/[^/]+\/library$/,
    handler: () => ({ status: 200, body: [] }),
  },
  {
    method: "POST",
    pattern: /^\/projects\/[^/]+\/library$/,
    handler: (_url, body) => {
      const payload = (body ?? {}) as Record<string, unknown>;
      return {
        status: 201,
        body: {
          id: "lib-stub-1",
          project_id: "example-project",
          kind: payload.kind ?? "prompt",
          name: payload.name ?? "",
          description: payload.description ?? "",
          content_ref: payload.content_ref ?? null,
          tags: payload.tags ?? [],
          status: "ACTIVE",
          created_at: "2026-09-14T00:00:00Z",
          updated_at: "2026-09-14T00:00:00Z",
        },
      };
    },
  },
  // PLAN-045 EC-03 second batch + PLAN-059：ops 读写投影（alerts/incidents/rules/schedules/data-health）。
  ...OPS_ROUTES,
  // PLAN-060 EC-05：Tool Provider 目录 + 注册治理写面（目录随注册状态变化）。
  ...REGISTRY_ROUTES,
  // PLAN-046 EC-04: budget adjust + reserved-vs-consumed forecast.
  ...BUDGET_ROUTES,
  // PLAN-049 WP-C: capability policy snapshot.
  ...POLICY_ROUTES,
  // PLAN-052 WP-D: experiment queue + plan list (G14).
  ...EXPERIMENT_QUEUE_ROUTES,
  // PLAN-055 WP-B: run + project lineage (G9).
  ...LINEAGE_ROUTES,
  // PLAN-058 WP-D: workspace snapshot capability / files / file-level diff (G8).
  ...WORKSPACE_ROUTES,
];
