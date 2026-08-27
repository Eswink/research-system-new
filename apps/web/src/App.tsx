import { useState } from "react";

import { ApprovalsPanel } from "./features/approvals/ApprovalsPanel";
import { EndpointsHome } from "./features/endpoints/EndpointsHome";
import { InspectionPanel } from "./features/inspection/InspectionPanel";
import { ModelsPage } from "./features/models/ModelsPage";
import { DryRunPanel } from "./features/protocol/DryRunPanel";
import { RunPanel } from "./features/runs/RunPanel";
import { RelayWizard } from "./features/setup/RelayWizard";
import { TeamPage } from "./features/team/TeamPage";
import { WorkspaceView } from "./features/workspace/WorkspaceView";
import { useEndpoints } from "./hooks/useEndpoints";
import type { LlmEndpointReadDto } from "./api/types";

export type ConsoleView = "console" | "models" | "team" | "workspace" | "experiments";

const NAV_ITEMS: { id: ConsoleView; label: string }[] = [
  { id: "console", label: "Console" },
  { id: "models", label: "Models" },
  { id: "team", label: "Team" },
  { id: "workspace", label: "Workspace & Experiments" },
];

/**
 * Research OS Console 入口。
 * 应用只消费 API DTO（server-state cache）；刷新后状态全部从 API 恢复，
 * 不持有 Canonical State，不写 localStorage。
 *
 * M13-R1（WP-B2/S5）：activeView state 驱动的真实 view-switcher：
 * Console / Models / Team / Workspace & Experiments 均为真实视图，
 * 无死链接。
 */
export function App() {
  const { endpoints, loading, error, refresh } = useEndpoints();
  const [activeView, setActiveView] = useState<ConsoleView>("console");

  if (loading) {
    return <div data-testid="app-loading">Loading console…</div>;
  }
  if (error !== null) {
    return (
      <div data-testid="app-error" role="alert">
        Backend unavailable: {error}
      </div>
    );
  }

  return (
    <div className="app">
      <ConsoleHeader
        activeView={activeView}
        onNavigate={setActiveView}
        hasEndpoints={endpoints.length > 0}
      />
      <main>
        {endpoints.length === 0 ? (
          <RelayWizard onComplete={refresh} />
        ) : (
          <ConsoleBody activeView={activeView} endpoints={endpoints} onAddRelay={refresh} />
        )}
      </main>
    </div>
  );
}

function ConsoleHeader({
  activeView,
  onNavigate,
  hasEndpoints,
}: {
  activeView: ConsoleView;
  onNavigate: (view: ConsoleView) => void;
  hasEndpoints: boolean;
}) {
  return (
    <header>
      <h1>Research OS Console</h1>
      {hasEndpoints && (
        <nav aria-label="console views">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={activeView === item.id ? "active" : ""}
              onClick={() => {
                onNavigate(item.id);
              }}
              data-testid={`nav-${item.id}`}
            >
              {item.label}
            </button>
          ))}
        </nav>
      )}
    </header>
  );
}

function ConsoleBody({
  activeView,
  endpoints,
  onAddRelay,
}: {
  activeView: ConsoleView;
  endpoints: LlmEndpointReadDto[];
  onAddRelay: () => void;
}) {
  if (activeView === "models") {
    return <ModelsPage />;
  }
  if (activeView === "team") {
    return <TeamPage />;
  }
  if (activeView === "workspace" || activeView === "experiments") {
    return <WorkspaceView />;
  }
  return (
    <>
      <EndpointsHome endpoints={endpoints} onAddRelay={onAddRelay} />
      <DryRunPanel />
      <RunPanel />
      <ApprovalsPanel />
      <InspectionPanel />
    </>
  );
}
