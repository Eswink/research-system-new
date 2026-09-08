import { useCallback, useEffect, useState } from "react";

import { DEFAULT_ROUTE, hashToRoute, routeToHash, type Route } from "./registry";
import {
  EMPTY_CONTEXT,
  parseContext,
  stripContext,
  withContext,
  type UrlContext,
} from "./urlContext";

export interface ResolvedRoute {
  route: Route;
  found: boolean;
  context: UrlContext;
}

/** hash 路由状态钩子：hashchange 驱动；未知地址进入 not-found（found=false）。 */
export function useHashRoute(): [ResolvedRoute, (route: Route, ctx?: UrlContext) => void] {
  const [resolved, setResolved] = useState<ResolvedRoute>(() => resolve(window.location.hash));

  useEffect(() => {
    const onHashChange = (): void => {
      setResolved(resolve(window.location.hash));
    };
    window.addEventListener("hashchange", onHashChange);
    return () => {
      window.removeEventListener("hashchange", onHashChange);
    };
  }, []);

  const navigate = useCallback((next: Route, ctx: UrlContext = EMPTY_CONTEXT) => {
    const hash = withContext(routeToHash(next), ctx);
    if (window.location.hash === hash) {
      setResolved({ route: next, found: true, context: ctx });
      return;
    }
    window.location.hash = hash;
  }, []);

  return [resolved, navigate];
}

function resolve(hash: string): ResolvedRoute {
  const context = parseContext(hash);
  const bare = stripContext(hash);
  if (bare === "" || bare === "#" || bare === "#/") {
    return { route: DEFAULT_ROUTE, found: true, context };
  }
  const route = hashToRoute(bare);
  return route === null
    ? { route: DEFAULT_ROUTE, found: false, context }
    : { route, found: true, context };
}
