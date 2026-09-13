import { pageSupport } from "./pageSupport";
import type { Route } from "./registry";

export type DataSource = "live" | "example";
export type SourceSelection = DataSource | "auto";

/** An absent backend contract, not a failed request, permits a labeled example page. */
export function resolveDataSource(route: Route, selection: SourceSelection): DataSource {
  if (selection !== "auto") return selection;
  // WP-C（PLAN-041）：portfolio/projects 已有真实注册表契约，不再强制 example。
  return pageSupport(route).level === "gap" ? "example" : "live";
}

export function parseSourceSelection(search: string): SourceSelection {
  const source = new URLSearchParams(search).get("source");
  return source === "live" || source === "example" ? source : "auto";
}
