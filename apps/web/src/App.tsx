import { useEffect, useMemo, useState } from "react";

import type { LlmEndpointReadDto } from "./api/types";
import { ApprovalsPanel } from "./features/approvals/ApprovalsPanel";
import { EndpointsHome } from "./features/endpoints/EndpointsHome";
import { InspectionPanel } from "./features/inspection/InspectionPanel";
import { ModelsPage } from "./features/models/ModelsPage";
import { OperationsPanel } from "./features/operations/OperationsPanel";
import { ProtocolDraftEditor } from "./features/protocol/editor/ProtocolDraftEditor";
import { RunPanel } from "./features/runs/RunPanel";
import { RelayWizard } from "./features/setup/RelayWizard";
import { TeamPage } from "./features/team/TeamPage";
import { WorkspaceView } from "./features/workspace/WorkspaceView";
import { useEndpoints } from "./hooks/useEndpoints";
import { I18nProvider } from "./i18n/I18nProvider";
import { AppShell } from "./layout/AppShell";
import {
  applyPreferences,
  loadPreferences,
  savePreferences,
  type ConsolePreferences,
} from "./layout/preferences";
import { SETUP_ROUTE } from "./navigation/routes";
import { useHashRoute } from "./navigation/useHashRoute";

/**
 * Research OS Console 入口。
 * 应用只消费 API DTO（server-state cache）；刷新后状态全部从 API 恢复。
 * 浏览器持久化仅限主题/密度/语言/编辑模式偏好（layout/preferences.ts）。
 *
 * 重建（PLAN-20260908-033）：接入 AppShell 外壳 + hash 路由；
 * 业务面板在阶段五逐页替换，此阶段先原样接入外壳保证功能可用。
 */
export function App() {
  const { endpoints, loading, error, refresh } = useEndpoints();
  const [preferences, setPreferences] = useState<ConsolePreferences>(() => loadPreferences());
  const [route, navigate] = useHashRoute();
  const [selectedRunId, setSelectedRunId] = useState("");
  const [showWizard, setShowWizard] = useState(false);

  useEffect(() => {
    applyPreferences(preferences);
    savePreferences(preferences);
  }, [preferences]);

  const language = preferences.language;
  const onLanguageChange = useMemo(
    () => (lang: "zh" | "en") => {
      setPreferences((prev) => ({ ...prev, language: lang }));
    },
    [],
  );

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
    <I18nProvider language={language} onLanguageChange={onLanguageChange}>
      <ConsoleRoot
        endpoints={endpoints}
        refresh={refresh}
        preferences={preferences}
        onPreferencesChange={setPreferences}
        route={route}
        navigate={navigate}
        selectedRunId={selectedRunId}
        onSelectedRunIdChange={setSelectedRunId}
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
  route: ReturnType<typeof useHashRoute>[0];
  navigate: ReturnType<typeof useHashRoute>[1];
  selectedRunId: string;
  onSelectedRunIdChange: (runId: string) => void;
  showWizard: boolean;
  onShowWizardChange: (show: boolean) => void;
}

function ConsoleRoot(props: ConsoleRootProps) {
  const { endpoints, route, navigate, showWizard, onShowWizardChange } = props;
  const isSetupRoute = route.domain === SETUP_ROUTE.domain;
  const wizardVisible = isSetupRoute || endpoints.length === 0 || showWizard;

  if (wizardVisible) {
    const closeWizard = (): void => {
      onShowWizardChange(false);
      if (isSetupRoute) {
        navigate({ domain: "plan", page: "protocol" });
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
  return (
    <AppShell
      route={`#/${route.domain}/${route.page}`}
      onNavigate={(hash) => {
        window.location.hash = hash;
      }}
      preferences={props.preferences}
      onPreferencesChange={props.onPreferencesChange}
      selectedRunId={props.selectedRunId}
      onSelectedRunIdChange={props.onSelectedRunIdChange}
      onOpenSetup={() => {
        onShowWizardChange(true);
      }}
    >
      <ConsoleBody
        route={`${route.domain}/${route.page}`}
        endpoints={endpoints}
        onAddRelay={() => {
          onShowWizardChange(true);
        }}
        selectedRunId={props.selectedRunId}
        onSelectedRunIdChange={props.onSelectedRunIdChange}
      />
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

function ConsoleBody({
  route,
  endpoints,
  onAddRelay,
  selectedRunId,
  onSelectedRunIdChange,
}: {
  route: string;
  endpoints: LlmEndpointReadDto[];
  onAddRelay: () => void;
  selectedRunId: string;
  onSelectedRunIdChange: (runId: string) => void;
}) {
  if (route === "assets/endpoints") {
    return <EndpointsHome endpoints={endpoints} onAddRelay={onAddRelay} />;
  }
  if (route === "assets/models") {
    return <ModelsPage />;
  }
  if (route === "plan/team") {
    return <TeamPage />;
  }
  if (route === "run/workspace") {
    return <WorkspaceView />;
  }
  if (route === "govern/operations") {
    return <OperationsPanel />;
  }
  if (route === "run/runs") {
    return (
      <RunPanel onRunSelected={onSelectedRunIdChange} initialRunId={selectedRunId} />
    );
  }
  if (route === "evidence/inspection") {
    return <InspectionPanel />;
  }
  if (route === "govern/approvals") {
    return <ApprovalsPanel />;
  }
  // plan/protocol（默认）：协议编辑器 + 预检报告（阶段四闭环；信息架构见
  // docs/frontend/CONSOLE_REBUILD.md §3——运行/审批/证据已拆分为独立域页面）
  return <ProtocolDraftEditor />;
}
