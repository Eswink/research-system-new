/**
 * 规范路由注册表（PLAN-20260908-034 T06）。
 *
 * 八域 33 条规范路由 + 三个全局页（settings/notifications/command-center）。
 * 导航、页面完整性测试与命令面板消费同一注册表；每条路由必须有独立页面身份。
 * 旧路由别名见 LEGACY_ALIASES（T32 兼容）。
 */

import type { IconName } from "../components/Icon";

export type DomainId =
  "plan" | "portfolio" | "run" | "library" | "evidence" | "insights" | "ops" | "govern";

export type PageId =
  | "overview"
  | "protocol"
  | "team"
  | "projects"
  | "experiments"
  | "runs-history"
  | "compare"
  | "timeline"
  | "approvals"
  | "workspace"
  | "prompts"
  | "datasets"
  | "notebooks"
  | "model-registry"
  | "lineage"
  | "endpoints"
  | "setup"
  | "claims"
  | "reports"
  | "cost-analytics"
  | "alerts"
  | "incidents"
  | "schedules"
  | "integrations"
  | "data-health"
  | "matrix"
  | "compute"
  | "observability"
  | "budget"
  | "audit";

/** 全局页（不在域侧栏内，经顶栏进入）。 */
export type MetaPageId = "settings" | "notifications" | "command-center";

export interface Route {
  domain: DomainId | MetaPageId;
  page: PageId | MetaPageId;
}

export interface DomainDef {
  id: DomainId;
  labelKey: string;
  icon: IconName;
  pages: readonly PageId[];
}

/** 八域定义——顺序即侧栏顺序（对齐设计 AppShell.jsx DOMAINS）。 */
export const DOMAINS: readonly DomainDef[] = [
  { id: "plan", labelKey: "dom.plan", icon: "book", pages: ["overview", "protocol", "team"] },
  {
    id: "portfolio",
    labelKey: "dom.portfolio",
    icon: "hex",
    pages: ["projects", "experiments", "runs-history", "compare"],
  },
  { id: "run", labelKey: "dom.run", icon: "graph", pages: ["timeline", "approvals", "workspace"] },
  {
    id: "library",
    labelKey: "dom.library",
    icon: "diamond",
    pages: ["prompts", "datasets", "notebooks", "model-registry", "lineage", "endpoints", "setup"],
  },
  { id: "evidence", labelKey: "dom.evidence", icon: "diamond", pages: ["claims"] },
  { id: "insights", labelKey: "dom.insights", icon: "graph", pages: ["reports", "cost-analytics"] },
  {
    id: "ops",
    labelKey: "dom.ops",
    icon: "shield",
    pages: [
      "alerts",
      "incidents",
      "schedules",
      "integrations",
      "data-health",
      "matrix",
      "compute",
      "observability",
    ],
  },
  { id: "govern", labelKey: "dom.govern", icon: "shield", pages: ["budget", "audit"] },
];

export const META_PAGES: readonly MetaPageId[] = ["settings", "notifications", "command-center"];

/** 全部 33 条规范路由（30 域内 + 3 全局）。 */
export const CANONICAL_ROUTES: readonly Route[] = [
  ...DOMAINS.flatMap((d) => d.pages.map((p) => ({ domain: d.id, page: p }))),
  ...META_PAGES.map((m) => ({ domain: m, page: m })),
];

/** 旧路由 → 规范路由别名（cursor plan §8）。 */
export const LEGACY_ALIASES: Readonly<Record<string, Route>> = {
  "assets/endpoints": { domain: "library", page: "endpoints" },
  "assets/models": { domain: "library", page: "model-registry" },
  "assets/compute": { domain: "ops", page: "compute" },
  "run/runs": { domain: "portfolio", page: "runs-history" },
  "evidence/inspection": { domain: "evidence", page: "claims" },
  "govern/approvals": { domain: "run", page: "approvals" },
  "govern/operations": { domain: "ops", page: "observability" },
  "setup/wizard": { domain: "library", page: "setup" },
};

export function isDomainId(value: string | undefined): value is DomainId {
  return value !== undefined && DOMAINS.some((d) => d.id === value);
}

export function isMetaPage(value: string | undefined): value is MetaPageId {
  return value !== undefined && META_PAGES.includes(value as MetaPageId);
}

export function domainOf(id: DomainId): DomainDef | undefined {
  return DOMAINS.find((d) => d.id === id);
}

export function isCanonicalRoute(route: Route): boolean {
  if (isMetaPage(route.domain)) {
    return route.domain === route.page;
  }
  const domain = domainOf(route.domain);
  return domain?.pages.includes(route.page as PageId) ?? false;
}

export function routeToHash(route: Route): string {
  return `#/${route.domain}/${route.page}`;
}

/** 解析 hash：规范路由直达；旧别名映射；未知进入 not-found 标记。 */
export function hashToRoute(hash: string): Route | null {
  const segments = hash
    .replace(/^#\/?/, "")
    .split("/")
    .filter((s) => s.length > 0);
  if (segments.length !== 2) {
    return null;
  }
  const key = `${segments[0] ?? ""}/${segments[1] ?? ""}`;
  const alias = LEGACY_ALIASES[key];
  if (alias !== undefined) {
    return alias;
  }
  if (isMetaPage(segments[0]) && segments[0] === segments[1]) {
    return { domain: segments[0], page: segments[0] };
  }
  if (isDomainId(segments[0])) {
    const domain = domainOf(segments[0]);
    const page = segments[1];
    if (domain !== undefined && page !== undefined && domain.pages.includes(page as PageId)) {
      return { domain: segments[0], page: page as PageId };
    }
  }
  return null;
}

export const DEFAULT_ROUTE: Route = { domain: "plan", page: "overview" };
