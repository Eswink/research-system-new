/**
 * 前端接入清单（PLAN-20260908-034 T06）。
 *
 * 记录每个页面/操作的已支持、部分支持、不可用及原因。
 * 这是前端接入清单，不是产品 Tool Capability，也不是授权判定。
 * 与 docs/frontend/CONSOLE_PAGE_MAP.md 同源维护。
 */

import type { Route } from "./registry";

export type SupportLevel = "full" | "partial" | "gap";

export interface PageSupport {
  level: SupportLevel;
  /** 缺口/限制说明（i18n key 或直接文案）。 */
  reason?: string;
  /** 被禁用的操作清单（用于逐操作禁用与说明）。 */
  disabledOperations?: readonly string[];
}

/** 后端能力缺口登记（cursor plan §3 / CONSOLE_PAGE_MAP.md）。 */
export const GAPS = {
  multiProject:
    "项目注册表已接入（GET/POST/PATCH/DELETE /projects；创建/归档/删除/上下文切换" +
    "真实生效，runs/settings/drafts 按项目归属）；删除仅对无引用项目可用（被运行/" +
    "草稿/实验队列/库资源/运维记录引用时 409 且不级联），默认项目为合成基线不可删；" +
    "agents/memory/experiments 数据面仍单项目共享，租户隔离属 M18 deferred",
  notifications:
    "通知已接入事件投影（GET /notifications + 已读持久化）；无实时推送，数量只来自当前页",
  account: "无账户/身份/Billing/平台 API Keys API",
  budgetAdjust:
    "预算调整已接入（interventions budget_adjust 走 BudgetLedger 的 release+reserve）；" +
    "预测只覆盖已预留额度（未预留开销不外推）；运行中语义变更（换 Agent/协议）仍 501",
  budgetForecast:
    "Run 级预留-消耗预测已接入（GET /runs/{id}/cost-forecast，仅已预留额度，不外推）；" +
    "项目级时序外推见 insights/cost-analytics（GET /projects/{id}/cost-forecast）",
  pauseResume:
    "pause/resume 为协作式执行协调：PAUSED 时派发面停止认领该 run 的任务（已持租约" +
    "不撤销），本进程执行器在 phase 边界停下；resume 恢复派发，只有持有暂停上下文时" +
    "才继续剩余任务（否则只解除暂停）。无抢占式中断；跨进程暂停上下文不持久化",
  fileBrowse:
    "制品内容 Diff 已接入（GET /artifacts/{left}/diff/{right}，二进制/超限如实标注）；" +
    "预览与下载已接入（GET /artifacts/{id}/content）；" +
    "工作区快照文件树与文件级 Diff 已接入（GET /workspace-snapshots/{digest}/files、" +
    "/workspace-snapshots/{left}/diff/{right}：按 digest 只读、文件级只比元数据）；" +
    "需配置 RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT，未配置时端点诚实 503；" +
    "控制面不持久化 run→工作区绑定，故只能回答「该 run 记录过哪些快照」",
  globalLineage:
    "项目级血缘已接入（GET /projects/{id}/lineage：项目内各 Run 的投影合并图，" +
    "共享节点即跨 Run 关系）；数据集/提示词与 Run 的引用关系无记录面，" +
    "库资源只作未连边清单呈现（响应内 reference_recording 如实标注），不猜测连边",
  delete:
    "端点/模型/草稿/用户 Agent/项目已接入 DELETE（被引用 → 409，项目附引用清单）；" +
    "memory 记录与契约基线（example role/template/agent、默认项目）不提供删除",
  approvalsEmpty:
    "审批注册点已接入（human-gate 协议暂停时注册，见 human_gate_demo_v1）；" +
    "无审批门的 run 列表为空是正确状态",
  costSeries:
    "项目级成本预测已接入（GET /projects/{id}/cost-forecast：对已计价的天取日均外推，" +
    "方法/样本天数/排除项与原因随响应返回；不插值、UNKNOWN 不当 0、跨币种不给金额）；" +
    "成本日序列见 GET /cost/daily",
  memory:
    "产品 Memory 已接入（WP-A 起 SQLite 开发路径与 PG canonical 双支持）；" +
    "无持久化 pending 提案，门链直提交；memory.write 已入 policy 面（逐 tier 判决" +
    "在 govern/audit 只读呈现，policy.yaml 变更需重启控制面）",
  experimentCreate:
    "计划预注册/归档与实验队列已接入（GET /experiment-plans、POST /projects/{id}/" +
    "experiments/{plan}/queue、GET/PATCH/DELETE /experiment-queue/{id}；派发由控制面" +
    "队列消费者按排期执行，at-least-once）；复现执行与日历/矩阵视图无 API，不伪装",
  prompts:
    "库目录已接入（GET /projects/{id}/library?kind=prompt + 创建/重命名/归档）；" +
    "版本树与 A-B 无 API，不伪造",
  datasets:
    "库目录已接入（kind=dataset 的引用登记）；上传与字段 schema 无 API；" +
    "评测输入仍由 eval spec 承载",
  notebooks:
    "库目录已接入（kind=notebook 的条目登记）；单元格编辑与执行无 API",
  reports:
    "已接入 GET /runs/{id}/deliverable（M12 持久化交付物）；" +
    "报告生成/编辑/PDF/发布无 API——生成动作禁用",
  alerts:
    "告警收件箱已接入（GET /projects/{id}/ops/alerts，派生自失败 Run/" +
    "非健康端点/离线 worker）+ 静音规则写面（POST/PATCH/DELETE /ops/alert-rules）；" +
    "规则只打 muted/muted_by 标记、不隐藏告警；未配置 OpsStore 时规则面 503 并如实标注",
  incidents:
    "事故处置已接入：POST /projects/{id}/ops/incidents 登记（可关联来源 run）、" +
    "POST /ops/incidents/{id}/assign 指派、POST /ops/incidents/{id}/close 关闭（写结论）；" +
    "关闭后不可再处置（409）；失败 Run 仍只作候选，不自动登记",
  schedules:
    "进程内 scheduler 配置事实已接入（GET /ops/schedules）；" +
    "无用户可见创建/启停/触发 API",
  integrations:
    "Tool Provider 目录与注册治理已接入（GET /tool-providers 目录 + 三态健康；" +
    "GET/POST /tool-provider-registrations、PATCH、approve/revoke/health-check）；" +
    "注册须 pin（sha256:<hex>），PENDING 不进目录、APPROVE 后进目录、REVOKE 为终态；" +
    "缺：provider 凭据绑定与工具包安装（ToolPack）仍无写面，健康探测不含 schema 漂移比对",
  dataHealth:
    "既有状态的可观测指标已接入（GET /projects/{id}/ops/data-health：端点健康计数/" +
    "dataset 计数/artifact 抽样校验）；无聚合质量报告 API",
} as const;

function routeKey(route: Route): string {
  return `${route.domain}/${route.page}`;
}

const SUPPORT: Readonly<Record<string, PageSupport>> = {
  "plan/overview": { level: "partial", reason: "聚合已加载数据；无独立 overview API" },
  "plan/protocol": { level: "full" },
  "plan/team": { level: "full" },
  "portfolio/projects": { level: "partial", reason: GAPS.multiProject },
  "portfolio/experiments": {
    level: "partial",
    reason: GAPS.experimentCreate,
    disabledOperations: ["reproduce-run"],
  },
  "portfolio/runs-history": { level: "full" },
  "portfolio/compare": { level: "partial", reason: "仅比较已返回指标；不可比语义保留" },
  "run/timeline": { level: "partial", reason: GAPS.pauseResume },
  "run/approvals": { level: "full" },
  "run/workspace": {
    level: "full",
    reason: GAPS.fileBrowse,
  },
  "library/prompts": {
    level: "partial",
    reason: GAPS.prompts,
    disabledOperations: ["version-tree", "ab-test"],
  },
  "library/datasets": {
    level: "partial",
    reason: GAPS.datasets,
    disabledOperations: ["upload", "schema"],
  },
  "library/notebooks": {
    level: "partial",
    reason: GAPS.notebooks,
    disabledOperations: ["cell-edit", "execute"],
  },
  "library/model-registry": { level: "full" },
  "library/lineage": { level: "partial", reason: GAPS.globalLineage },
  "library/endpoints": { level: "full" },
  "library/setup": { level: "full" },
  "evidence/claims": { level: "full" },
  "insights/reports": {
    level: "partial",
    reason: GAPS.reports,
    disabledOperations: ["generate", "edit", "export-pdf", "publish"],
  },
  "insights/cost-analytics": { level: "partial", reason: GAPS.costSeries },
  "ops/alerts": {
    level: "full",
    reason: GAPS.alerts,
  },
  "ops/incidents": {
    level: "full",
    reason: GAPS.incidents,
  },
  "ops/schedules": {
    level: "partial",
    reason: GAPS.schedules,
    disabledOperations: ["create", "toggle", "trigger"],
  },
  "ops/integrations": {
    level: "partial",
    reason: GAPS.integrations,
  },
  "ops/data-health": {
    level: "partial",
    reason: GAPS.dataHealth,
    disabledOperations: ["aggregate-report"],
  },
  "ops/matrix": { level: "gap", reason: "界面状态说明页（非实时运维状态）" },
  "ops/compute": { level: "full" },
  "ops/observability": { level: "full" },
  "govern/budget": { level: "partial", reason: GAPS.budgetForecast },
  "govern/audit": { level: "partial", reason: GAPS.memory },
  "settings/settings": {
    level: "partial",
    reason: GAPS.account,
    // SettingsPage 分区渲染判定唯一来源（WP-C：isOperationDisabled 消费）。
    disabledOperations: ["account", "security", "billing"],
  },
  "notifications/notifications": { level: "partial", reason: GAPS.notifications },
  "command-center/command-center": {
    level: "partial",
    reason: "复用真实查询；跨项目/预测/全球节点不可用",
  },
};

export function pageSupport(route: Route): PageSupport {
  return SUPPORT[routeKey(route)] ?? { level: "gap", reason: "未登记页面" };
}

export function isOperationDisabled(route: Route, operation: string): boolean {
  return pageSupport(route).disabledOperations?.includes(operation) === true;
}
