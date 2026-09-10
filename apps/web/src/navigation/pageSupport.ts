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
  multiProject: "无多项目管理 API：仅当前单项目上下文",
  notifications:
    "通知已接入事件投影（GET /notifications + 已读持久化）；无实时推送，数量只来自当前页",
  account: "无账户/身份/Billing/平台 API Keys API",
  budgetAdjust: "预算调整无契约（interventions budget_adjust 恒 501）",
  pauseResume: "pause/resume 仅状态迁移，不证明实际暂停/恢复执行",
  fileBrowse: "文件 Diff 无接口；预览与下载已接入（GET /artifacts/{id}/content）",
  globalLineage: "全局数据集/提示词血缘无 API：仅 Run 级引用",
  delete: "控制面无 DELETE 端点：不提供删除操作",
  approvalsEmpty: "生产路径审批列表恒空（ApprovalStore 无注册点）",
  costSeries:
    "成本日序列已接入（GET /cost/daily）；预测/前瞻无 API，不绘制",
  memory:
    "产品 Memory 已接入（PG canonical state；SQLite 开发路径 503）；" +
    "无持久化 pending 提案，门链直提交；capability policy 面扩展为 follow-up",
  experimentCreate:
    "计划预注册/归档已接入（仅 PG canonical state；SQLite 开发路径 503）；" +
    "域内无队列状态，排队/调度无 API，不伪装",
  prompts: "无 prompts API",
  datasets: "无 datasets API",
  notebooks: "无 notebooks API",
  reports: "无 reports API",
  alerts: "无告警规则/收件箱 API",
  incidents: "无事件处置 API",
  schedules: "无用户可见调度 API",
  integrations: "无 Tool Provider 管理 API",
  dataHealth: "无聚合数据健康 API",
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
    disabledOperations: ["create", "archive", "delete", "switch-workspace"],
  },
  "portfolio/experiments": {
    level: "partial",
    reason: GAPS.experimentCreate,
    disabledOperations: ["queue", "schedule"],
  },
  "portfolio/runs-history": { level: "full" },
  "portfolio/compare": { level: "partial", reason: "仅比较已返回指标；不可比语义保留" },
  "run/timeline": { level: "full" },
  "run/approvals": { level: "partial", reason: GAPS.approvalsEmpty },
  "run/workspace": {
    level: "partial",
    reason: GAPS.fileBrowse,
    disabledOperations: ["file-browse", "file-preview", "file-diff"],
  },
  "library/prompts": { level: "gap", reason: GAPS.prompts },
  "library/datasets": { level: "gap", reason: GAPS.datasets },
  "library/notebooks": { level: "gap", reason: GAPS.notebooks },
  "library/model-registry": { level: "full" },
  "library/lineage": { level: "partial", reason: GAPS.globalLineage },
  "library/endpoints": { level: "full", disabledOperations: ["delete"] },
  "library/setup": { level: "full" },
  "evidence/claims": { level: "full" },
  "insights/reports": { level: "gap", reason: GAPS.reports },
  "insights/cost-analytics": { level: "partial", reason: GAPS.costSeries },
  "ops/alerts": { level: "gap", reason: GAPS.alerts },
  "ops/incidents": { level: "gap", reason: GAPS.incidents },
  "ops/schedules": { level: "gap", reason: GAPS.schedules },
  "ops/integrations": { level: "gap", reason: GAPS.integrations },
  "ops/data-health": { level: "gap", reason: GAPS.dataHealth },
  "ops/matrix": { level: "gap", reason: "界面状态说明页（非实时运维状态）" },
  "ops/compute": { level: "full" },
  "ops/observability": { level: "full" },
  "govern/budget": { level: "partial", reason: GAPS.budgetAdjust, disabledOperations: ["adjust"] },
  "govern/audit": { level: "partial", reason: GAPS.memory },
  "settings/settings": {
    level: "partial",
    reason: GAPS.account,
    disabledOperations: ["account", "platform-keys", "2fa", "billing"],
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
