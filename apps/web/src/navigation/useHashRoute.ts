import { useCallback, useEffect, useRef, useState } from "react";
import { NAVIGATION_COMMITTED, requestNavigation } from "./navigationGuard";
import { DEFAULT_ROUTE, hashToRoute, routeToHash, type Route } from "./registry";
import { parseContext, stripContext, withContext, type UrlContext } from "./urlContext";

export interface ResolvedRoute {
  route: Route;
  found: boolean;
  context: UrlContext;
}

/** One URL owner, including browser history; preserve run/draft identity across
 * sidebar navigation.
 */
export function useHashRoute(): [ResolvedRoute, (route: Route, ctx?: UrlContext) => void] {
  const [resolved, setResolved] = useState<ResolvedRoute>(() => resolve(window.location.hash));
  const committed = useRef(window.location.href);
  const accepted = useRef<string | null>(null);
  useEffect(() => bindNavigation({ committed, accepted, setResolved }), []);
  const navigate = useCallback((next: Route, ctx?: UrlContext) => {
    const hash = withContext(routeToHash(next), ctx ?? parseContext(window.location.hash));
    if (window.location.hash === hash) return;
    const url = new URL(window.location.href);
    url.hash = hash;
    if (!requestNavigation(url.href)) return;
    accepted.current = url.href;
    window.location.hash = hash;
  }, []);
  return [resolved, navigate];
}

function bindNavigation({
  committed,
  accepted,
  setResolved,
}: {
  committed: { current: string };
  accepted: { current: string | null };
  setResolved: (route: ResolvedRoute) => void;
}) {
  const onNavigation = () => {
    const destination = window.location.href;
    if (destination === committed.current) return;
    if (accepted.current !== destination && !requestNavigation(destination)) {
      window.history.replaceState(null, "", committed.current);
      return;
    }
    accepted.current = null;
    committed.current = destination;
    setResolved(resolve(window.location.hash));
  };
  const onCommit = () => {
    committed.current = window.location.href;
    setResolved(resolve(window.location.hash));
  };
  window.addEventListener("hashchange", onNavigation);
  window.addEventListener("popstate", onNavigation);
  window.addEventListener(NAVIGATION_COMMITTED, onCommit);
  return () => {
    window.removeEventListener("hashchange", onNavigation);
    window.removeEventListener("popstate", onNavigation);
    window.removeEventListener(NAVIGATION_COMMITTED, onCommit);
  };
}

function resolve(hash: string): ResolvedRoute {
  const context = parseContext(hash);
  const bare = stripContext(hash);
  if (bare === "" || bare === "#" || bare === "#/")
    return { route: DEFAULT_ROUTE, found: true, context };
  const route = hashToRoute(bare);
  return route === null
    ? { route: DEFAULT_ROUTE, found: false, context }
    : { route, found: true, context };
}
