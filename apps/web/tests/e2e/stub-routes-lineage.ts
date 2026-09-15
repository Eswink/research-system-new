/**
 * 来源血缘 API 替身路由（PLAN-20260915-055 WP-B，G9）。
 *
 * 形状遵循真实 DTO（services/api/dto/inspection.py）：
 * - run 级：`LineageDto`（nodes/edges typed 投影）；
 * - 项目级：`ProjectLineageDto`（合并图 + 未连边库资源清单 + reference_recording）；
 * - run scope 依赖：`GET /runs/{id}/claims`（`ClaimMapDto`）与 `/evidence`
 *   （`list[EvidenceDto]`）——血缘页选中 run 后会取这两个端点的真值，替身缺了
 *   它们就会 500（严格替身视为未接入）；此处给出受控空态。
 *
 * 替身给出一条由两个 run 共享的来源节点（`shared=true`）与一条未连边数据集，
 * 让设计基线覆盖"跨运行共享"这一核心视觉态；run 级保持空图（页面两种状态都渲染）。
 */

import type { StubRoute } from "./stub-routes";

const SHARED_SOURCE = "paper://shared-2024";

export const LINEAGE_ROUTES: readonly StubRoute[] = [
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/claims$/,
    handler: () => ({
      status: 200,
      body: { claims: [], unsupported_claims: [], contradictory_claims: [], degraded: false },
    }),
  },
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/evidence$/,
    handler: () => ({ status: 200, body: [] }),
  },
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/lineage$/,
    handler: (url) => ({
      status: 200,
      body: {
        run_id: url.pathname.split("/")[2] ?? "",
        nodes: [],
        edges: [],
        global_lineage_available: false,
        global_lineage_reason: "项目级血缘见 GET /projects/{id}/lineage",
        degraded: false,
      },
    }),
  },
  {
    method: "GET",
    pattern: /^\/projects\/[^/]+\/lineage$/,
    handler: (url) => ({
      status: 200,
      body: {
        project_id: url.pathname.split("/")[2] ?? "",
        run_count: 2,
        nodes: [
          { id: "run:r-1", kind: "run", label: "r-1", run_ids: ["r-1"], shared: false },
          { id: "run:r-2", kind: "run", label: "r-2", run_ids: ["r-2"], shared: false },
          {
            id: `source:${SHARED_SOURCE}`,
            kind: "source",
            label: SHARED_SOURCE,
            run_ids: ["r-1", "r-2"],
            shared: true,
          },
        ],
        edges: [
          {
            source: `source:${SHARED_SOURCE}`,
            target: "evidence:ev-1",
            relation: "cited_by",
          },
        ],
        library_resources: [
          { id: "ds-1", kind: "dataset", name: "benchmark-v1", status: "ACTIVE" },
          { id: "pr-1", kind: "prompt", name: "critic-v2", status: "ACTIVE" },
        ],
        reference_recording: "NOT_RECORDED",
        reference_recording_reason:
          "run 与数据集/提示词的引用关系无记录面：库资源以未连边清单呈现",
        degraded: false,
        degraded_reason: null,
      },
    }),
  },
];
