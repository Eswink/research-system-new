import { pageSupport } from "./pageSupport";
import type { Route } from "./registry";

export type DataSource = "live" | "example";
export type SourceSelection = DataSource | "auto";

/** An absent backend contract, not a failed request, permits a labeled example page. */
export function resolveDataSource(route: Route, selection: SourceSelection): DataSource {
  if (selection !== "auto") return selection;
  const key = `${route.domain}/${route.page}`;
  return pageSupport(route).level === "gap" || key === "portfolio/projects" ? "example" : "live";
}

export function parseSourceSelection(search: string): SourceSelection {
  const source = new URLSearchParams(search).get("source");
  return source === "live" || source === "example" ? source : "auto";
}
