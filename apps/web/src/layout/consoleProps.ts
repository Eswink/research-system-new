import type { Route } from "../navigation/registry";
import type { UrlContext } from "../navigation/urlContext";
import type { ResolvedRoute } from "../navigation/useHashRoute";
import type { ConsolePreferences } from "./preferences";

export interface ConsoleProps {
  resolved: ResolvedRoute;
  navigate: (route: Route, context?: UrlContext) => void;
  preferences: ConsolePreferences;
  onPreferencesChange: (preferences: ConsolePreferences) => void;
}
