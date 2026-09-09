import type { Route } from "./registry";

/** Only first-visit onboarding and endpoint management depend on the endpoint list. */
export function needsEndpointList(route: Route, runId: string): boolean {
  return (
    isFirstVisitRoute(route, runId) || (route.domain === "library" && route.page === "endpoints")
  );
}

export function isFirstVisitRoute(route: Route, runId: string): boolean {
  return route.domain === "plan" && route.page === "overview" && runId === "";
}
