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
    "项目注册表已接入（GET/POST/PATCH /projects；创建/归档/上下文切换真实生效，" +
    "runs/settings/drafts 按项目归属）；不提供删除（归档即终态），" +
    "agents/memory/experiments 数据面仍单项目共享，租户隔离属 M18 deferred",
  notifications:
    "通知已接入事件投影（GET /notifications + 已读持久化）；无实时推送，数量只来自当前页",
  account: "无账户/身份/Billing/平台 API Keys API",
  budgetAdjust:
    "预算调整已接入（interventions budget_adjust 走 BudgetLedger 的 release+reserve）；" +
    "预测只覆盖已预留额度（未预留开销不外推）；运行中语义变更（换 Agent/协议）仍 501",
  budgetForecast: "Run 级预留-消耗预测已接入（GET /runs/{id}/cost-forecast）；无 burn-rate 外推",
  pauseResume:
    "pause/resume 为协作式执行协调：PAUSED 时派发面停止认领该 run 的任务（已持租约" +
    "不撤销），本进程执行器在 phase 边界停下；resume 恢复派发，只有持有暂停上下文时" +
    "才继续剩余任务（否则只解除暂停）。无抢占式中断；跨进程暂停上下文不持久化",
  fileBrowse:
    "制品内容 Diff 已接入（GET /artifacts/{left}/diff/{right}，二进制/超限如实标注）；" +
    "预览与下载已接入（GET /artifacts/{id}/content）；工作区文件树与文件级快照 Diff 无 API",
  globalLineage:
    "全局数据集/提示词血缘无 API（仅 Run 级引用，已接入 GET /runs/{id}/lineage 投影）",
  delete:
    "端点/模型/草稿/用户 Agent 已接入 DELETE（被引用 → 409）；" +
    "memory 记录与契约基线（example role/template/agent）不提供删除",
  approvalsEmpty:
    "审批注册点已接入（human-gate 协议暂停时注册，见 human_gate_demo_v1）；" +
    "无审批门的 run 列表为空是正确状态",
  costSeries:
    "成本日序列已接入（GET /cost/daily）；Run 级预留-消耗预测已接入" +
    "（GET /runs/{id}/cost-forecast，仅已预留额度）；跨 run 时间序列预测不绘制",
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
    "只读告警收件箱已接入（GET /projects/{id}/ops/alerts，派生自失败 Run/" +
    "非健康端点/离线 worker）；规则 CRUD 无 API",
  incidents:
    "失败 Run 候选列表已接入（GET /projects/{id}/ops/incidents）；" +
    "无 declare/assign/close 处置工作流，失败 Run 不自动登记为事故",
  schedules:
    "进程内 scheduler 配置事实已接入（GET /ops/schedules）；" +
    "无用户可见创建/启停/触发 API",
  integrations:
    "Tool Provider 目录已接入（GET /tool-providers + 三态健康）；" +
    "install/approve/revoke 属供应链治理面（G15），不提供",
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
  "portfolio/projects": {
    level: "partial",
    reason: GAPS.multiProject,
    disabledOperations: ["delete"],
  },
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
    level: "partial",
    reason: GAPS.fileBrowse,
    disabledOperations: ["file-browse", "file-preview", "file-diff"],
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
    level: "partial",
    reason: GAPS.alerts,
    disabledOperations: ["new-rule", "edit-rule", "delete-rule"],
  },
  "ops/incidents": {
    level: "partial",
    reason: GAPS.incidents,
    disabledOperations: ["declare", "assign", "close"],
  },
  "ops/schedules": {
    level: "partial",
    reason: GAPS.schedules,
    disabledOperations: ["create", "toggle", "trigger"],
  },
  "ops/integrations": {
    level: "partial",
    reason: GAPS.integrations,
    disabledOperations: ["install", "approve", "revoke"],
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
