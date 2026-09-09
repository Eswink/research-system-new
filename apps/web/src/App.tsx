import { Suspense } from "react";
import { LiveConsole } from "./LiveConsole";
import { ExampleConsole } from "./features/example-console/ExampleConsole";
import { I18nProvider } from "./i18n/I18nProvider";
import { ConsoleFrame } from "./layout/ConsoleFrame";
import { ConsoleLoading } from "./layout/ConsoleLoading";
import type { ConsoleProps } from "./layout/consoleProps";
import { useConsolePreferences } from "./layout/useConsolePreferences";
import { NotFoundPage } from "./navigation/NotFoundPage";
import { pageSupport } from "./navigation/pageSupport";
import { PresentationContext } from "./navigation/presentationContext";
import { resolveDataSource } from "./navigation/presentationPolicy";
import { DEFAULT_ROUTE } from "./navigation/registry";
import { useHashRoute } from "./navigation/useHashRoute";
import { useSourceSelection } from "./navigation/useSourceSelection";

/** One URL/preference owner, separately loaded data-source trees and separately loaded routes. */
export function App() {
  const [preferences, setPreferences] = useConsolePreferences();
  const [resolved, navigate] = useHashRoute();
  const [selection, setSource] = useSourceSelection();
  const source = resolveDataSource(resolved.route, selection);
  const props = { resolved, navigate, preferences, onPreferencesChange: setPreferences };
  return (
    <I18nProvider
      language={preferences.language}
      onLanguageChange={(language) => {
        setPreferences((previous) => ({ ...previous, language }));
      }}
    >
      <PresentationContext.Provider
        value={{ source, selection, setSource, reason: pageSupport(resolved.route).reason ?? "" }}
      >
        <ConsoleContent props={props} source={source} />
      </PresentationContext.Provider>
    </I18nProvider>
  );
}

function ConsoleContent({
  props,
  source,
}: {
  props: ConsoleProps;
  source: ReturnType<typeof resolveDataSource>;
}) {
  if (!props.resolved.found)
    return (
      <ConsoleFrame {...props}>
        <NotFoundPage
          onHome={() => {
            props.navigate(DEFAULT_ROUTE);
          }}
        />
      </ConsoleFrame>
    );
  const routeKey = `${props.resolved.route.domain}/${props.resolved.route.page}`;
  return (
    <Suspense fallback={<ConsoleLoading {...props} />}>
      {source === "example" ? (
        <ExampleConsole key={`example:${routeKey}`} {...props} />
      ) : (
        <LiveConsole {...props} />
      )}
    </Suspense>
  );
}

export { routeToHash } from "./navigation/registry";
