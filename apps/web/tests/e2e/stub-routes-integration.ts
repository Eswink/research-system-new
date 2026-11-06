/**
 * 联调补齐的四类读/写面替身（GOAL-20261103-104 EC-03）。
 *
 * 覆盖本轮新接线的路由：研究方向写面、研究程序四条、评审判词、以及三条「只加 client +
 * 白名单登记」的路由。**未注册的请求会让 e2e 立刻失败**（`stub-api` 的
 * `assertNoUnmatched`）——所以新接线必须同轮补替身，否则页面一挂载就会因为
 * 未替身请求而红。
 *
 * 形状照抄 `docs/api/openapi.m13.json`：只保留读面会用到的字段。
 */

import type { StubRoute } from "./stub-routes";

const STAMP = "2026-11-03T00:00:00+00:00";

/** 研究方向：模块级可变状态（写面要能看出来「真的变了」）。 */
let direction: string | null = "提高小样本分类的稳健性";

/** 一条程序的最小读面形状（`ProgramDetailDto`）。 */
const PROGRAM = {
  id: "program-1",
  project_id: "example-project",
  protocol_id: "direction_to_manuscript_v1",
  max_runs: 3,
  continue_on_verdicts: ["PASS"],
  // GOAL-20261107-107 EC-02：TS 类型补齐后这些字段在夹具里也必须在场（否则夹具与
  // 服务端 DTO 不同形，"类型漂移"与"夹具缺字段"会混成同一种红）。
  max_attempts_per_index: 1,
  human_gate_at_index: null,
  human_gate_on_verdicts: null,
  human_gate_at_indexes: null,
  gate_nudge_after_seconds: null,
  human_gate_hybrid: null,
  created_at: STAMP,
  updated_at: STAMP,
  runs: [],
  decisions: [],
  run_count: 0,
};

/**
 * 一条**已有决定**的程序（GOAL-20261107-107 EC-02 的正例臂）。
 *
 * `PROGRAM` 的 `decisions` 是空的 —— 那覆盖「没有决定就明确空态」；这一条覆盖
 * 「有决定就逐条列出来，且 `cited_facts` 可展开」。两条**不能**共用一个夹具：
 * 空数组与两个决定是互斥的事实。
 */
const PROGRAM_WITH_DECISIONS = {
  ...PROGRAM,
  id: "program-2",
  run_count: 2,
  runs: [
    { run_id: "run-a", program_index: 0, state: "SUCCEEDED", manifest_digest: null },
    { run_id: "run-b", program_index: 1, state: "FAILED", manifest_digest: null },
  ],
  decisions: [
    {
      after_index: 0,
      kind: "CONTINUE",
      reason: "previous verdict passed the continue-on list",
      cited_run_id: "run-a",
      cited_facts: ["verdict=PASS", "state=SUCCEEDED"],
      decided_at: STAMP,
    },
    {
      after_index: 1,
      kind: "STOP",
      reason: "verdict left the continue-on list",
      cited_run_id: "run-b",
      cited_facts: ["verdict=REJECT"],
      decided_at: STAMP,
    },
  ],
};

/** 一条评审判词（`ReviewFindingDto`）：`reviewer_model` 非空，归因可见。 */
const REVIEW = {
  id: "review-1",
  run_id: "eleven-phases",
  task_id: "task-review",
  contract_id: "review-contract",
  review_type: "novelty",
  verdict: "fail",
  findings: ["NOVELTY_THRESHOLD: 0.41 < 0.50", "EVIDENCE_COVERAGE: 2 >= 1 sources"],
  reviewed_by: "reviewer-agent",
  reviewed_at: STAMP,
  reviewer_model: "main/glm-5.3",
};

export function resetIntegrationStub(): void {
  direction = "提高小样本分类的稳健性";
}

export const INTEGRATION_ROUTES: readonly StubRoute[] = [
  // ── 研究方向写面（PUT /projects/{id}/direction）──
  {
    method: "PUT",
    pattern: /^\/projects\/[^/]+\/direction$/,
    handler: (_url, body) => {
      const patch = (body ?? {}) as { direction?: string | null };
      direction = patch.direction ?? null;
      return {
        status: 200,
        body: {
          id: "example-project",
          name: "Example ML Research",
          status: "ACTIVE",
          created_at: STAMP,
          updated_at: STAMP,
          direction,
        },
      };
    },
  },
  // ── 研究程序四条 ──
  {
    method: "GET",
    pattern: /^\/projects\/[^/]+\/programs$/,
    handler: () => ({ status: 200, body: [PROGRAM, PROGRAM_WITH_DECISIONS] }),
  },
  {
    method: "POST",
    pattern: /^\/projects\/[^/]+\/programs$/,
    handler: () => ({ status: 201, body: PROGRAM }),
  },
  {
    method: "GET",
    pattern: /^\/programs\/[^/]+$/,
    handler: (url) => {
      // 按 id 分流：`program-2` 带两条决定（正例臂），其余回落最小形状。
      const id = url.pathname.replace(/^\/api/, "").split("/")[2] ?? "";
      const body = id === PROGRAM_WITH_DECISIONS.id ? PROGRAM_WITH_DECISIONS : PROGRAM;
      return { status: 200, body };
    },
  },
  {
    method: "POST",
    pattern: /^\/programs\/[^/]+\/advance$/,
    handler: () => ({
      status: 200,
      body: {
        program_id: PROGRAM.id,
        decision: {
          after_index: 0,
          kind: "CONTINUE",
          reason: "previous verdict passed the continue-on list",
          cited_run_id: null,
          cited_facts: ["verdict=PASS"],
          decided_at: STAMP,
        },
        started_run_id: "run-1",
        run_count: 1,
      },
    }),
  },
  // ── 评审判词（GET /runs/{id}/reviews）──
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/reviews$/,
    handler: () => ({ status: 200, body: [REVIEW] }),
  },
  // ── 三条「只加 client + 白名单登记」的路由：替身在场，但 UI 并不调用 ──
  {
    method: "GET",
    pattern: /^\/library\/[^/]+$/,
    handler: () => ({
      status: 200,
      body: {
        id: "lib-1",
        kind: "prompt",
        name: "reviewer prompt",
        description: "stub",
        content_ref: null,
        tags: [],
        status: "ACTIVE",
        created_at: STAMP,
        updated_at: STAMP,
      },
    }),
  },
  {
    method: "GET",
    pattern: /^\/projects\/[^/]+\/memory\/validity$/,
    handler: () => ({
      status: 200,
      body: { at: STAMP, scope_note: "stub", records: [] },
    }),
  },
  {
    method: "POST",
    pattern: /^\/tasks\/[^/]+\/retry$/,
    handler: () => ({
      status: 200,
      body: {
        task_id: "task-1",
        run_id: "run-1",
        contract_id: "contract-1",
        role_id: "researcher",
        state: "PENDING",
      },
    }),
  },
];
