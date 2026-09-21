/**
 * Run 详情读面的替身路由（GOAL-20260918-006 cycle 3 = EC-03）。
 *
 * 此前替身里没有 `GET /runs/{id}`：运行页只能在"未选择 run"的空壳下取基线，
 * `RunDetailDto.rebuild`（重建就绪读面）没有页面级验证入口。本文件补上 run 详情
 * 及页面同步请求的两个子读（tasks/events）。
 *
 * 三条 fixture 正好落在分类器的三个状态上
 * （`packages/application/run_orchestration/rebuild_readiness.py`）：
 *
 * - 记录自足：两个 digest + 冻结正文都在行上；
 * - 依赖来源：两个 digest 齐、无冻结正文，来源仍可解析；
 * - 拒绝：四个事实全缺（旧 run 形态），`missing` 按**行字段名**逐个点名。
 *
 * 读面不预测重建结果：状态只说"记录够不够重建"。
 */

import type { RunDetailDto } from "../../src/api/types";
import type { StubRoute } from "./stub-routes";

const STAMP = "2026-09-18T00:00:00Z";

/** 三个 run × 分类器的三个状态（页面三态可区分的受控输入）。 */
export const REBUILD_RUNS: readonly RunDetailDto[] = [
  {
    id: "rebuild-self-contained",
    project_id: "example-project",
    protocol_id: "sort-analysis",
    state: "SUCCEEDED",
    manifest_digest: "sha256:frozen-manifest",
    manifest_semantic_digest: "sha256:frozen-semantics",
    protocol_body_digest: "sha256:frozen-body",
    paused_dispatch: null,
    dispatch: null,
    rebuild: { status: "SELF_CONTAINED", missing: [] },
    execution: null,
    created_at: STAMP,
    updated_at: STAMP,
  },
  {
    id: "rebuild-source-dependent",
    project_id: "example-project",
    protocol_id: "sort-analysis",
    state: "SUCCEEDED",
    manifest_digest: "sha256:frozen-manifest",
    manifest_semantic_digest: "sha256:frozen-semantics",
    protocol_body_digest: null,
    paused_dispatch: null,
    dispatch: null,
    rebuild: { status: "SOURCE_DEPENDENT", missing: [] },
    execution: null,
    created_at: STAMP,
    updated_at: STAMP,
  },
  {
    id: "rebuild-refused",
    project_id: "example-project",
    protocol_id: "sort-analysis",
    state: "FAILED",
    manifest_digest: null,
    manifest_semantic_digest: null,
    protocol_body_digest: null,
    paused_dispatch: null,
    dispatch: null,
    rebuild: {
      status: "REFUSED",
      missing: ["manifest_digest", "manifest_semantic_digest", "protocol_body", "protocol_source"],
    },
    execution: null,
    created_at: STAMP,
    updated_at: STAMP,
  },
  // 执行体披露的两个受控输入（GOAL-007 cycle 4 = EC-04）：同一条读面上只有
  // execution_backend 不同——页面若把两者渲染成同一种，对应 e2e 即红。
  {
    id: "substrate-openhands",
    project_id: "example-project",
    protocol_id: "sort-analysis",
    state: "SUCCEEDED",
    manifest_digest: "sha256:frozen-manifest",
    manifest_semantic_digest: "sha256:frozen-semantics",
    protocol_body_digest: "sha256:frozen-body",
    paused_dispatch: null,
    dispatch: null,
    rebuild: { status: "SELF_CONTAINED", missing: [] },
    execution: {
      execution_backend: "openhands",
      runtime_fingerprint: {
        status: "NOT_VERIFIED",
        substrate: "openhands",
        reason: "runtime selected but no model probe fact was collected for this run",
        // GOAL-010 EC-04：没有实测记录 ⇒ 冻结占位，四要素全空且逐项点名。
        source: "FROZEN_PLACEHOLDER",
        endpoint_config_digest: null,
        returned_model_identifier: null,
        probe_suite_digest: null,
        system_fingerprint: null,
        observed_model_identifiers: [],
        missing_fields: [
          "endpoint_config_digest",
          "probe_suite_digest",
          "returned_model_identifier",
          "system_fingerprint",
        ],
      },
    },
    created_at: STAMP,
    updated_at: STAMP,
  },
  {
    id: "substrate-fake",
    project_id: "example-project",
    protocol_id: "sort-analysis",
    state: "SUCCEEDED",
    manifest_digest: "sha256:frozen-manifest",
    manifest_semantic_digest: "sha256:frozen-semantics",
    protocol_body_digest: "sha256:frozen-body",
    paused_dispatch: null,
    dispatch: null,
    rebuild: { status: "SELF_CONTAINED", missing: [] },
    execution: {
      execution_backend: "fake",
      runtime_fingerprint: {
        status: "NOT_VERIFIED",
        substrate: "fake",
        reason:
          "no model probe was run for this run: the controlled demo runtime makes no model call",
        source: "FROZEN_PLACEHOLDER",
        endpoint_config_digest: null,
        returned_model_identifier: null,
        probe_suite_digest: null,
        system_fingerprint: null,
        observed_model_identifiers: [],
        missing_fields: [
          "endpoint_config_digest",
          "probe_suite_digest",
          "returned_model_identifier",
          "system_fingerprint",
        ],
      },
    },
    created_at: STAMP,
    updated_at: STAMP,
  },
  // 第四态：**已冻结但没声明执行体**（`execution_backend: null`）——必须与「未冻结」
  // （`execution: null`）在页面上分开说，否则两种情况会被渲染成同一个词。
  {
    id: "substrate-undeclared",
    project_id: "example-project",
    protocol_id: "sort-analysis",
    state: "SUCCEEDED",
    manifest_digest: "sha256:frozen-manifest",
    manifest_semantic_digest: "sha256:frozen-semantics",
    protocol_body_digest: "sha256:frozen-body",
    paused_dispatch: null,
    dispatch: null,
    rebuild: { status: "SELF_CONTAINED", missing: [] },
    execution: { execution_backend: null, runtime_fingerprint: null },
    created_at: STAMP,
    updated_at: STAMP,
  },
];

export const RUN_ROUTES: readonly StubRoute[] = [
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+$/,
    handler: (url) => {
      // `/api/runs/{id}` ⇒ 段 [:index 3]（0 是空串、1 是 api、2 是 runs）。
      const id = url.pathname.split("/")[3] ?? "";
      const found = REBUILD_RUNS.find((item) => item.id === id);
      if (found === undefined) {
        return {
          status: 404,
          body: {
            type: "about:blank",
            title: "Run not found",
            status: 404,
            detail: `no stub run ${id}`,
            instance: url.pathname,
          },
        };
      }
      return { status: 200, body: found };
    },
  },
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/tasks$/,
    handler: () => ({ status: 200, body: [] }),
  },
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/events$/,
    handler: () => ({ status: 200, body: [] }),
  },
];
