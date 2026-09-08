import { useEffect, useState } from "react";

import type { LlmEndpointReadDto } from "./api/types";
import { RelayWizard } from "./features/setup/RelayWizard";
import { useEndpoints } from "./hooks/useEndpoints";
import { I18nProvider } from "./i18n/I18nProvider";
import { AppShell } from "./layout/AppShell";
import {
  applyPreferences,
  loadPreferences,
  savePreferences,
  type ConsolePreferences,
} from "./layout/preferences";
import { NotFoundPage } from "./navigation/NotFoundPage";
import { PageRenderer, type PageContext } from "./navigation/PageRenderer";
import { DEFAULT_ROUTE, routeToHash, type Route } from "./navigation/registry";
import type { UrlContext } from "./navigation/urlContext";
import { useHashRoute } from "./navigation/useHashRoute";

/**
 * Research OS Console 入口（PLAN-20260908-034 高保真重建）。
 * App.tsx 只组合 Provider、外壳与路由页面；页面分派经 PageRenderer 注册表，
 * 未知地址进入明确未找到页。业务数据从 API 获取；浏览器持久化仅限界面偏好。
 */
export function App() {
  const { endpoints, loading, error, refresh } = useEndpoints();
  const [preferences, setPreferences] = useState<ConsolePreferences>(() => loadPreferences());
  const [resolved, navigate] = useHashRoute();
  const [showWizard, setShowWizard] = useState(false);

  useEffect(() => {
    applyPreferences(preferences);
    savePreferences(preferences);
  }, [preferences]);

  if (loading) {
    return (
      <div data-testid="app-loading" style={{ padding: 24 }}>
        Loading console…
      </div>
    );
  }
  if (error !== null) {
    return (
      <div data-testid="app-error" role="alert" style={{ padding: 24 }}>
        Backend unavailable: {error}
      </div>
    );
  }
  return (
    <I18nProvider
      language={preferences.language}
      onLanguageChange={(lang) => { setPreferences((prev) => ({ ...prev, language: lang })); }}
    >
      <ConsoleRoot
        endpoints={endpoints}
        refresh={refresh}
        preferences={preferences}
        onPreferencesChange={setPreferences}
        route={resolved.route}
        found={resolved.found}
        navigate={navigate}
        context={resolved.context}
        showWizard={showWizard}
        onShowWizardChange={setShowWizard}
      />
    </I18nProvider>
  );
}

interface ConsoleRootProps {
  endpoints: LlmEndpointReadDto[];
  refresh: () => void;
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
  route: Route;
  found: boolean;
  navigate: (route: Route, ctx?: UrlContext) => void;
  context: UrlContext;
  showWizard: boolean;
  onShowWizardChange: (show: boolean) => void;
}

function ConsoleRoot(props: ConsoleRootProps) {
  const { endpoints, route, found, navigate, context, showWizard, onShowWizardChange } = props;
  const isSetupRoute = route.domain === "library" && route.page === "setup";
  const wizardVisible = isSetupRoute || endpoints.length === 0 || showWizard;

  if (wizardVisible) {
    const closeWizard = (): void => {
      onShowWizardChange(false);
      if (isSetupRoute) {
        navigate(DEFAULT_ROUTE);
      }
    };
    return (
      <WizardSurface
        endpointsCount={endpoints.length}
        onComplete={props.refresh}
        {...(endpoints.length === 0 ? {} : { onCancel: closeWizard })}
      />
    );
  }
  const ctx: PageContext = {
    endpoints,
    onAddRelay: () => { onShowWizardChange(true); },
    selectedRunId: context.runId,
    onSelectedRunIdChange: (runId) => { navigate(route, { ...context, runId }); },
    onOpenSetup: () => { onShowWizardChange(true); },
    preferences: props.preferences,
    onPreferencesChange: props.onPreferencesChange,
  };
  return (
    <AppShell
      route={route}
      onNavigate={(hash) => { window.location.hash = hash; }}
      preferences={props.preferences}
      onPreferencesChange={props.onPreferencesChange}
      onOpenCommandCenter={() => {
        navigate({ domain: "command-center", page: "command-center" });
      }}
      onOpenNotifications={() => {
        navigate({ domain: "notifications", page: "notifications" });
      }}
    >
      {found ? (
        <PageRenderer route={route} ctx={ctx} />
      ) : (
        <NotFoundPage onHome={() => { navigate(DEFAULT_ROUTE); }} />
      )}
    </AppShell>
  );
}

/** 首次接入向导保留为独立全屏流程 */
function WizardSurface({
  endpointsCount,
  onComplete,
  onCancel,
}: {
  endpointsCount: number;
  onComplete: () => void;
  onCancel?: (() => void) | undefined;
}) {
  return (
    <div style={{ minHeight: "100vh", padding: 24 }}>
      {endpointsCount > 0 && onCancel !== undefined && (
        <button type="button" className="btn sm" onClick={onCancel} data-testid="wizard-cancel">
          ← Console
        </button>
      )}
      <RelayWizard onComplete={onComplete} />
    </div>
  );
}

export { routeToHash };
