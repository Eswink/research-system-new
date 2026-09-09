import type { ReactNode } from "react";
import { hashToRoute } from "../navigation/registry";
import { AppShell } from "./AppShell";
import type { ConsoleProps } from "./consoleProps";

/** Shared frame: route/context ownership stays above live and example renderers. */
export function ConsoleFrame({ children, ...props }: ConsoleProps & { children: ReactNode }) {
  const { resolved, navigate, preferences, onPreferencesChange } = props;
  return (
    <AppShell
      runId={resolved.context.runId}
      route={resolved.route}
      preferences={preferences}
      onPreferencesChange={onPreferencesChange}
      onNavigate={(hash) => {
        const route = hashToRoute(hash);
        if (route) navigate(route, resolved.context);
      }}
      onOpenCommandCenter={() => {
        navigate({ domain: "command-center", page: "command-center" }, resolved.context);
      }}
      onOpenNotifications={() => {
        navigate({ domain: "notifications", page: "notifications" }, resolved.context);
      }}
    >
      {children}
    </AppShell>
  );
}
