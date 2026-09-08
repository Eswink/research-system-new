/**
 * 类型化 hash 路由（无路由框架）。
 * 形如 `#/plan/protocol`；支持刷新恢复、前进后退与直达。
 * 只保存界面路由；业务数据仍从 API 获取。
 */

export const PLAN_DOMAINS = ["plan"] as const;
export const ROUTE_DOMAINS = ["plan", "run", "evidence", "assets", "govern", "setup"] as const;

export type RouteDomain = (typeof ROUTE_DOMAINS)[number];

export interface Route {
  domain: RouteDomain;
  page: string;
}

export const SETUP_ROUTE: Route = { domain: "setup", page: "wizard" };

/** 每个域的合法页面与其默认页（信息架构见 docs/frontend/CONSOLE_REBUILD.md §3） */
export const DOMAIN_PAGES: Record<Exclude<RouteDomain, "setup">, readonly string[]> = {
  plan: ["protocol", "team"],
  run: ["runs", "workspace"],
  evidence: ["inspection"],
  assets: ["endpoints", "models", "compute"],
  govern: ["approvals", "operations"],
};

export const DOMAIN_DEFAULT_PAGE: Record<Exclude<RouteDomain, "setup">, string> = {
  plan: "protocol",
  run: "runs",
  evidence: "inspection",
  assets: "endpoints",
  govern: "approvals",
};

export function routeToHash(route: Route): string {
  return `#/${route.domain}/${route.page}`;
}

export function hashToRoute(hash: string): Route {
  const segments = hash.replace(/^#\/?/, "").split("/").filter((s) => s.length > 0);
  if (segments[0] === "setup") {
    return SETUP_ROUTE;
  }
  const domain = segments[0];
  if (isRouteDomain(domain) && domain !== "setup") {
    const page = segments[1];
    if (page !== undefined && DOMAIN_PAGES[domain].includes(page)) {
      return { domain, page };
    }
    return { domain, page: DOMAIN_DEFAULT_PAGE[domain] };
  }
  return { domain: "plan", page: DOMAIN_DEFAULT_PAGE.plan };
}

function isRouteDomain(value: string | undefined): value is RouteDomain {
  return value !== undefined && (ROUTE_DOMAINS as readonly string[]).includes(value);
}
