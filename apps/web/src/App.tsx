import { ApprovalsPanel } from "./features/approvals/ApprovalsPanel";
import { EndpointsHome } from "./features/endpoints/EndpointsHome";
import { InspectionPanel } from "./features/inspection/InspectionPanel";
import { DryRunPanel } from "./features/protocol/DryRunPanel";
import { RunPanel } from "./features/runs/RunPanel";
import { RelayWizard } from "./features/setup/RelayWizard";
import { useEndpoints } from "./hooks/useEndpoints";

/**
 * Research OS Console 入口。
 * 应用只消费 API DTO（server-state cache）；刷新后状态全部从 API 恢复，
 * 不持有 Canonical State，不写 localStorage。
 */
export function App() {
  const { endpoints, loading, error, refresh } = useEndpoints();

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
      <header>
        <h1>Research OS Console</h1>
        {endpoints.length > 0 && (
          <nav>
            <a href="#/endpoints">Endpoints</a>
            <a href="#/models">Models</a>
          </nav>
        )}
      </header>
      <main>
        {endpoints.length === 0 ? (
          <RelayWizard onComplete={refresh} />
        ) : (
          <EndpointsHome endpoints={endpoints} onAddRelay={refresh} />
        )}
        {endpoints.length > 0 && <DryRunPanel />}
        {endpoints.length > 0 && <RunPanel />}
        {endpoints.length > 0 && <ApprovalsPanel />}
        {endpoints.length > 0 && <InspectionPanel />}
      </main>
    </div>
  );
}