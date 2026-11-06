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

import type { ArtifactDto, PhaseProgressDto, RunDetailDto } from "../../src/api/types";
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
    program_id: null,
    program_index: null,
    phases: null,
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
    program_id: null,
    program_index: null,
    phases: null,
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
    program_id: null,
    program_index: null,
    phases: null,
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
    program_id: null,
    program_index: null,
    phases: null,
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
    program_id: null,
    program_index: null,
    phases: null,
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
    program_id: null,
    program_index: null,
    phases: null,
    created_at: STAMP,
    updated_at: STAMP,
  },
];

/**
 * **十一相**的受控 run（GOAL-20261101-103 EC-03）。
 *
 * 相集与 `examples/protocols/direction_to_manuscript_v1.yaml` 的 11 个 `id` **逐字一致**
 * （判据 `run-phase-progress.spec.ts` 按这个名单核对节点）；四个状态**各至少出现一次**
 * ——否则「状态色互不相同」这条没有对象。
 */
export const ELEVEN_PHASES: readonly PhaseProgressDto[] = (
  [
    { phase_id: "question", strategy: "single_agent", state: "SUCCEEDED" },
    { phase_id: "retrieval", strategy: "single_agent", state: "SUCCEEDED" },
    { phase_id: "novelty", strategy: "single_agent", state: "SUCCEEDED" },
    { phase_id: "plan", strategy: "single_agent", state: "SUCCEEDED" },
    { phase_id: "experiment", strategy: "deterministic", state: "SUCCEEDED" },
    { phase_id: "review", strategy: "parallel_agents", state: "FAILED" },
    { phase_id: "manuscript", strategy: "single_agent", state: "RUNNING" },
    { phase_id: "editorial", strategy: "single_agent", state: "RUNNING" },
    { phase_id: "revision", strategy: "single_agent", state: "PENDING" },
    { phase_id: "submission", strategy: "single_agent", state: "PENDING" },
    { phase_id: "report", strategy: "deterministic", state: "PENDING" },
  ] as const
).map((phase) => ({
  ...phase,
  // 前两相有真实产出（点击展开要看得见），其余为空 —— 两个方向都在受控输入里。
  artifact_ids:
    phase.phase_id === "question"
      ? ["task-q:research_question"]
      : phase.phase_id === "retrieval"
        ? ["task-r:retrieval_report"]
        : [],
  started_at: phase.state === "PENDING" ? null : STAMP,
  completed_at: phase.state === "SUCCEEDED" ? STAMP : null,
}));

/** 十一相 run 的详情 fixture（其余字段与既有 fixture 同形，只换 id 与 phases）。 */
export const ELEVEN_PHASE_RUN: RunDetailDto = {
  id: "eleven-phases",
  project_id: "example-project",
  protocol_id: "direction_to_manuscript_v1_0_0",
  state: "RUNNING",
  manifest_digest: "sha256:frozen-manifest",
  manifest_semantic_digest: "sha256:frozen-semantics",
  protocol_body_digest: "sha256:frozen-body",
  paused_dispatch: null,
  dispatch: null,
  rebuild: { status: "SELF_CONTAINED", missing: [] },
  execution: { execution_backend: "openhands", runtime_fingerprint: null },
  program_id: null,
  program_index: null,
  phases: [...ELEVEN_PHASES],
  created_at: STAMP,
  updated_at: STAMP,
};

/** 旧 run 形态：**没有冻结协议正文** ⇒ 相结构读不到（`phases: null`）。 */
export const NO_BODY_RUN: RunDetailDto = {
  ...ELEVEN_PHASE_RUN,
  id: "no-frozen-body",
  protocol_body_digest: null,
  phases: null,
};

/** 全部 run fixture（既有重建读面六条 + 本轮两条：十一相 / 无冻结正文）。 */
const RUN_FIXTURES: readonly RunDetailDto[] = [
  ...REBUILD_RUNS,
  ELEVEN_PHASE_RUN,
  NO_BODY_RUN,
];

export const RUN_ROUTES: readonly StubRoute[] = [
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+$/,
    handler: (url) => {
      // `/api/runs/{id}` ⇒ 段 [:index 3]（0 是空串、1 是 api、2 是 runs）。
      const id = url.pathname.split("/")[3] ?? "";
      const found = RUN_FIXTURES.find((item) => item.id === id);
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
  // GOAL-20261101-103 EC-04：**手稿链**的制品读面。
  {
    method: "GET",
    pattern: /^\/runs\/([^/]+)\/artifacts$/,
    handler: (url) => {
      const runId = url.pathname.split("/")[3] ?? "";
      if (runId === "manuscript-run") return { status: 200, body: MANUSCRIPT_CHAIN };
      // 只有 v1 的 run（GOAL-20261107-107 EC-01 的**反证臂**：没有改稿就没有并排面板）。
      if (runId === "single-manuscript-run") {
        return { status: 200, body: MANUSCRIPT_CHAIN.slice(0, 1) };
      }
      // 其余 run 保持**既有 503 语义**（原来在 `stub-routes.ts` 的兜底里；那条被本路由
      // 取代了 ⇒ 语义搬到这里，逐字不变：artifact store not configured）。
      return {
        status: 503,
        body: {
          type: "about:blank",
          title: "Artifact Store Unavailable",
          status: 503,
          detail: "artifact store not configured",
          instance: "/artifacts",
        },
      };
    },
  },
  // 制品正文（ReportsPage 的手稿渲染与编辑决定解析都读它）。
  {
    method: "GET",
    // 文本制品正文：**逐字原文**（`bodyKind: "text"`；JSON 序列化会把 Markdown 包成带引号的串）。
    bodyKind: "text",
    pattern: /^\/artifacts\/([^/]+)\/content$/,
    handler: (url) => {
      const artifactId = decodeURIComponent(url.pathname.split("/")[3] ?? "");
      const body = MANUSCRIPT_CONTENTS[artifactId];
      if (body === undefined) return { status: 404, body: { detail: "no stub" } };
      return { status: 200, body };
    },
  },
  // 两制品内容 diff（GOAL-20261107-107 EC-01：改稿面板用它做 v1 → v2 并排）。
  //
  // **必须排在单制品元数据之前**：`/artifacts/{id}/diff/{other}` 与 `/artifacts/{id}`
  // 是两条路由，前者多两段路径；若后者先匹配（正则带锚点则不会，但顺序依赖仍是不该有的
  // 隐含契约）就会把 diff 请求吃成「取元数据」。
  {
    method: "GET",
    pattern: /^\/artifacts\/([^/]+)\/diff\/([^/]+)$/,
    handler: (url) => {
      // **去掉 `/api` 前缀再切段**：`url.pathname` 带部署前缀，按它切会让索引整体偏移一格
      // （实测：`parts[2]` 取到 `artifacts`，于是两次查找都 miss ⇒ 404 "no stub"）。
      const parts = url.pathname.replace(/^\/api/, "").split("/");
      const left = decodeURIComponent(parts[2] ?? "");
      const right = decodeURIComponent(parts[4] ?? "");
      const leftText = MANUSCRIPT_CONTENTS[left];
      const rightText = MANUSCRIPT_CONTENTS[right];
      if (leftText === undefined || rightText === undefined) {
        return { status: 404, body: { detail: "no stub" } };
      }
      return { status: 200, body: diffFixture({ left, right, leftText, rightText }) };
    },
  },
  // 单制品元数据（ArtifactBrowser 的详情面板）。
  {
    method: "GET",
    pattern: /^\/artifacts\/([^/]+)$/,
    handler: (url) => {
      const artifactId = decodeURIComponent(url.pathname.split("/")[3] ?? "");
      const found = MANUSCRIPT_CHAIN.find((item) => item.id === artifactId);
      if (found === undefined) return { status: 404, body: { detail: "no stub" } };
      return { status: 200, body: found };
    },
  },
];

/**
 * diff 夹具（与 `ArtifactDiffDto` 同形的最小可用版本）。
 *
 * 只做**逐行集合差**：两侧相同的行算 `CONTEXT`，只在右侧出现的算 `ADDED`，只在左侧出现
 * 的算 `REMOVED`。这够判「面板把三种行分别渲染」，而**不**冒充后端的 LCS 实现 ——
 * 真算法的判据在 Python 侧（`tests/api/` 与 `packages/application/artifacts/diff.py`）。
 */
function diffFixture(sides: { left: string; right: string; leftText: string; rightText: string }) {
  const { left, right, leftText, rightText } = sides;
  const leftLines = leftText.split("\n");
  const rightLines = rightText.split("\n");
  const rightSet = new Set(rightLines);
  const leftSet = new Set(leftLines);
  const lines = [
    ...leftLines
      .filter((line) => !rightSet.has(line))
      .map((text) => ({ kind: "REMOVED" as const, text })),
    ...rightLines
      .filter((line) => !leftSet.has(line))
      .map((text) => ({ kind: "ADDED" as const, text })),
    ...rightLines
      .filter((line) => leftSet.has(line))
      .map((text) => ({ kind: "CONTEXT" as const, text })),
  ];
  return {
    left_digest: `sha256:${left.replaceAll(":", "-")}`,
    right_digest: `sha256:${right.replaceAll(":", "-")}`,
    comparison: "LINE",
    available: true,
    identical: leftText === rightText,
    reason: null,
    lines,
    stats: {
      added: lines.filter((line) => line.kind === "ADDED").length,
      removed: lines.filter((line) => line.kind === "REMOVED").length,
      context: lines.filter((line) => line.kind === "CONTEXT").length,
    },
    truncated: false,
    note: "stub diff (line-set)",
  };
}

/** 一件制品 fixture（与 `ArtifactDto` 同形；本文件只用受控输入）。 */
function artifact(
  id: string,
  mediaType: string,
  overrides: Partial<ArtifactDto> = {},
): ArtifactDto {
  return {
    id,
    digest: `sha256:${id.replaceAll(":", "-")}`,
    size_bytes: 128,
    media_type: mediaType,
    state: "STAGED",
    created_by: "model:main/glm-5.3",
    source_refs: [],
    classification: null,
    retention_policy: "KEEP_FOREVER",
    created_at: STAMP,
    verified: null,
    supersedes: null,
    ...overrides,
  };
}

/**
 * 手稿链受控制品（GOAL-20261101-103 EC-04）。
 *
 * 覆盖三种受判形态：
 * - 命名约定 `{task_id}:{name}` 的 `manuscript.md` / `manuscript_v2.md`（有改稿链）；
 * - 裸名字形态（live 读面偶尔直接给 `editorial_decision`）；
 * - 一个**不在闭集里**的制品（`tool-result:xyz`）：它必须**没有**标签 —— 未命中不伪造。
 */
const MANUSCRIPT_CHAIN: readonly ArtifactDto[] = [
  artifact("task-m:manuscript.md", "text/markdown"),
  artifact("task-m:manuscript_v2.md", "text/markdown", {
    supersedes: "task-m:manuscript.md",
  }),
  artifact("editorial_decision", "application/json"),
  artifact("task-m:cover_letter.md", "text/markdown"),
  artifact("task-m:author_contributions.md", "text/markdown"),
  artifact("task-m:conflicts_of_interest.md", "text/markdown"),
  artifact("task-m:data_availability.md", "text/markdown"),
  artifact("task-m:supplementary.md", "text/markdown"),
  artifact("tool-result:xyz", "application/json"),
];

const MANUSCRIPT_MD = [
  "# A study of sorting",
  "",
  "## Abstract",
  "",
  "We study comparison sorting on small integer arrays and report the observed ordering.",
  "",
  "## Results",
  "",
  "The sorted array matched the reference ordering for every sampled input [1].",
].join("\n");

const EDITORIAL_JSON = JSON.stringify({
  editorial_decision: {
    decision: "major_revision",
    rationale: "the related work needs a stronger comparison baseline",
    required_changes: ["add a baseline", "discuss limitations"],
    target_journal: "Journal of Sorting Studies",
  },
});

const MANUSCRIPT_CONTENTS: Readonly<Record<string, string>> = {
  "task-m:manuscript.md": MANUSCRIPT_MD,
  // v2 **既加也改**（GOAL-20261107-107 EC-01）：只替换结尾会让 diff 只出现 `ADDED` 行，
  // 那样「删除行也分别渲染」这条判据就没有对象 —— 夹具必须两种行都能产生。
  "task-m:manuscript_v2.md": `${MANUSCRIPT_MD.replace(
    "We study comparison sorting on small integer arrays",
    "We study comparison sorting on arrays of up to sixteen integers",
  )}\n\n## Limitations\n\nWe only test small arrays.\n`,
  editorial_decision: EDITORIAL_JSON,
};
