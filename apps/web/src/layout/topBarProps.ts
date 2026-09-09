import type { Route } from "../navigation/registry";
import type { ConsolePreferences } from "./preferences";

export interface TopBarProps {
  route: Route;
  runId?: string | null | undefined;
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
  onOpenPalette: () => void;
  onOpenCommandCenter: () => void;
  onOpenNotifications: () => void;
  onNavigate: (hash: string) => void;
}
