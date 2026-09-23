/**
 * GOAL-20260923-013 EC-03 的**判据性质披露登记册**（单一来源）。
 *
 * 前三个 cycle 把每条判据「能被什么按压 / 不能被什么按压」散写在各自的 RECHECK 里；
 * 这里收成一份机器可读的登记册，由 `frontend-criteria-disclosure.test.ts` 机械强制：
 * ① **无遗漏**——本 GOAL 新增的每个 spec 文件里解析出的每条 test 都必须在册，且不许多出；
 * ② **两字段非空**——`pressTarget`（能被什么按压）与 `insensitiveFace`（不能被什么按压）
 *    都必须是非空字符串（禁止只写「判据绿」）；
 * ③ **披露与证据一致**——`sensitiveFace === "page"` 的条目必须引用一条 `press` 类证据。
 *
 * **为什么要有「不敏感面」这一栏**：本 GOAL 的 live 判据形态是「页面 == 读面」，
 * 两边**同源**（DOM 的值由读面响应导出）⇒ **改数据对它不敏感**（两边一起变，等式仍成立）。
 * 这类判据必须靠按压**页面那一段**（把渲染值钉成常量）才敏感。披露这件事本身是 EC-03 的验收内容。
 *
 * 实测证据（`scratch/` 不进仓库）：
 * - 按页面按压（数据不敏感的反面）：6 个 spec 共 **12** 条 test 各有红证，见 `evidence` 列；
 * - 按**数据**按压（证明披露「数据不敏感」为真）：`goal013-c4-spotcheck-data.txt` ⇒ **2 passed**
 *   （把 provider id 在 `examples/config/tool_providers.yaml` 里改名 ⇒ 读面与页面一起变 ⇒ 等式仍成立），
 *   同组成对：`goal013-c4-spotcheck-page.txt` ⇒ **2 failed**（按页面即红）。
 */

export type SensitiveFace = "page" | "structure";

export interface CriterionDisclosure {
  /** 相对 `apps/web` 的 spec 路径。 */
  readonly spec: string;
  /** live suite 名，或 `unit`。 */
  readonly suite: string;
  /** 该 spec 内的 test 名（逐字）。 */
  readonly testTitle: string;
  /** 能被什么按压（EC-03 的「按压对象」栏）。 */
  readonly pressTarget: string;
  /** **不能**被什么按压（EC-03 的「不敏感面」栏）。 */
  readonly insensitiveFace: string;
  /** 实际敏感的那一面。 */
  readonly sensitiveFace: SensitiveFace;
  /**
   * 成对反证的**前提**是否数据敏感。
   * 「等式数据不敏感」与「前提数据敏感」是两件事：把某一侧改成空，红的会是**前提**
   * （`toBeGreaterThan(0)` 之类的自证），而不是等式。披露必须分开写。
   */
  readonly premiseIsDataSensitive: boolean;
  /** 红证（按页面/按结构按压）与绿证（按数据按压）的 `scratch/` 路径。 */
  readonly evidence: readonly string[];
}

const PAGE_PRESS = "把组件渲染的值钉成常量（按页面按压）";
const DATA_INSENSITIVE =
  "改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的";
const STRUCTURE_PRESS = "改矩阵文本事实（行终态 / 缺口 token / 引文 / 删 LIVE:）";
const STRUCTURE_INSENSITIVE = "改被点名 spec 的**断言强度**——本判据是结构判据，不读断言强弱";

interface LiveRef {
  readonly spec: string;
  readonly suite: string;
  readonly testTitle: string;
  readonly evidence: readonly string[];
}

function live(ref: LiveRef): CriterionDisclosure {
  return {
    spec: ref.spec,
    suite: ref.suite,
    testTitle: ref.testTitle,
    pressTarget: PAGE_PRESS,
    insensitiveFace: DATA_INSENSITIVE,
    sensitiveFace: "page",
    premiseIsDataSensitive: true,
    evidence: ref.evidence,
  };
}

function structural(testTitle: string, evidence: readonly string[]): CriterionDisclosure {
  return {
    spec: "tests/unit/console-real-data-matrix.test.ts",
    suite: "unit",
    testTitle,
    pressTarget: STRUCTURE_PRESS,
    insensitiveFace: STRUCTURE_INSENSITIVE,
    sensitiveFace: "structure",
    premiseIsDataSensitive: false,
    evidence,
  };
}

export const CRITERIA_DISCLOSURE: readonly CriterionDisclosure[] = [
  // ---- 离线逐页矩阵判据（cycle 1；结构与语义分开：这是结构判据）----
  structural("① 矩阵完备：恰好 20 行，终态二选一，零条待定", [
    "scratch/goal013-c4-press-matrix-undecided.txt",
  ]),
  structural("② 三方同源：非 full 路由无遗漏；收敛行在代码里确为 full；缺口引文逐字来自权威", [
    "scratch/goal013-c1-press-matrix.txt",
  ]),
  structural("③ 收敛有证：每条收敛行点名的 live 用例存在、在白名单内、且真的驱动该路由并对 DOM 断言", [
    "scratch/goal013-c1-press-live-route.txt",
  ]),
  structural("④ 不混写：收敛行不带缺口 token，保持行不带 LIVE:", [
    "scratch/goal013-c4-press-matrix-mixed.txt",
  ]),

  // ---- 页面级 live「页面 == 读面」判据（cycles 1–3）----
  live({
    spec: "tests/e2e/live-plan-overview.spec.ts",
    suite: "plan-overview",
    testTitle: "live: 概览页的四张指标卡 == 读面（页面 == 读面）",
    evidence: ["scratch/goal013-c1-pressA-page.txt"],
  }),
  live({
    spec: "tests/e2e/live-plan-overview.spec.ts",
    suite: "plan-overview",
    testTitle: "live: 读面为空时页面显示诚实空态（成对反证，不伪造数据）",
    evidence: ["scratch/goal013-c1-pressA-page.txt"],
  }),
  live({
    spec: "tests/e2e/live-library-lineage.spec.ts",
    suite: "library-lineage",
    testTitle: "live: 血缘页的三张表与合并摘要 == 读面（页面 == 读面）",
    evidence: ["scratch/goal013-c2-press-lineage-rows.txt"],
  }),
  live({
    spec: "tests/e2e/live-library-lineage.spec.ts",
    suite: "library-lineage",
    testTitle: "live: 库资源读面为空时显示诚实空态，且不渲染空表（成对反证）",
    evidence: ["scratch/goal013-c2-press-empty-text.txt"],
  }),
  live({
    spec: "tests/e2e/live-govern-audit.spec.ts",
    suite: "govern-audit",
    testTitle: "live: 审计页的事件行数 == 读面（页面 == 读面）",
    evidence: ["scratch/goal013-c2-press-audit-rows.txt"],
  }),
  live({
    spec: "tests/e2e/live-govern-audit.spec.ts",
    suite: "govern-audit",
    testTitle: "live: 事件读面为空时显示诚实空态，且不渲染事件行（成对反证）",
    evidence: ["scratch/goal013-c4-press-audit-empty.txt"],
  }),
  live({
    spec: "tests/e2e/live-portfolio-experiments.spec.ts",
    suite: "portfolio-experiments",
    testTitle: "live: 实验表的逐行计数 == 读面（页面 == 读面）",
    evidence: ["scratch/goal013-c3-press-experiments.txt"],
  }),
  live({
    spec: "tests/e2e/live-portfolio-experiments.spec.ts",
    suite: "portfolio-experiments",
    testTitle: "live: 指标为空的实验渲染 0，不补占位指标（成对反证）",
    evidence: ["scratch/goal013-c3-press-experiments.txt"],
  }),
  live({
    spec: "tests/e2e/live-insights-reports.spec.ts",
    suite: "insights-reports",
    testTitle:
      "live: 交付物读面非空时，" + "报告页渲染的是读面的值（页面 == 读面）",
    evidence: ["scratch/goal013-c3-press-reports.txt"],
  }),
  live({
    spec: "tests/e2e/live-insights-reports.spec.ts",
    suite: "insights-reports",
    testTitle:
      "live: 无交付物的 run 显示读面给出的原因，" + "且不渲染来源区块（成对反证）",
    evidence: ["scratch/goal013-c4-press-reports-empty.txt"],
  }),
  live({
    spec: "tests/e2e/live-ops-integrations.spec.ts",
    suite: "ops-integrations",
    testTitle: "live: provider 目录逐行逐值 == 读面（页面 == 读面）",
    evidence: [
      "scratch/goal013-c3-press-integrations.txt",
      "scratch/goal013-c4-spotcheck-page.txt",
      "scratch/goal013-c4-spotcheck-data.txt",
    ],
  }),
  live({
    spec: "tests/e2e/live-ops-integrations.spec.ts",
    suite: "ops-integrations",
    testTitle: "live: 无法判定的 provider 如实显示 UNKNOWN，不伪装健康（成对反证）",
    evidence: [
      "scratch/goal013-c3-press-integrations.txt",
      "scratch/goal013-c4-spotcheck-page.txt",
      "scratch/goal013-c4-spotcheck-data.txt",
    ],
  }),
];

/** 本 GOAL 新增的判据文件（D-1 的枚举口径）。 */
export const CRITERIA_SPECS: readonly string[] = [
  "tests/unit/console-real-data-matrix.test.ts",
  "tests/e2e/live-plan-overview.spec.ts",
  "tests/e2e/live-library-lineage.spec.ts",
  "tests/e2e/live-govern-audit.spec.ts",
  "tests/e2e/live-portfolio-experiments.spec.ts",
  "tests/e2e/live-insights-reports.spec.ts",
  "tests/e2e/live-ops-integrations.spec.ts",
];
