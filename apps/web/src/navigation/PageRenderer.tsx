import { AlertsPage } from "../features/alerts/AlertsPage";
import { ApprovalsPanel } from "../features/approvals/ApprovalsPanel";
import { BudgetPage } from "../features/budget/BudgetPage";
import { CostAnalyticsPage } from "../features/cost-analysis/CostAnalyticsPage";
import { DataHealthPage } from "../features/data-health/DataHealthPage";
import { DatasetsPage } from "../features/datasets/DatasetsPage";
import { EndpointsHome } from "../features/endpoints/EndpointsHome";
import { ExperimentsPage } from "../features/experiments/ExperimentsPage";
import { GapPage } from "../features/gap/GapPage";
import { GovernancePage } from "../features/governance/GovernancePage";
import { IncidentsPage } from "../features/incidents/IncidentsPage";
import { InspectionPanel } from "../features/inspection/InspectionPanel";
import { IntegrationsPage } from "../features/integrations/IntegrationsPage";
import { LineagePage } from "../features/lineage/LineagePage";
import { ModelsPage } from "../features/models/ModelsPage";
import { NotebooksPage } from "../features/notebooks/NotebooksPage";
import { NotificationsPage } from "../features/notifications/NotificationsPage";
import { ComputePage } from "../features/operations/ComputePage";
import { OperationsPanel } from "../features/operations/OperationsPanel";
import { OverviewPage } from "../features/overview/OverviewPage";
import { ProjectsPage } from "../features/projects/ProjectsPage";
import { PromptsPage } from "../features/prompts/PromptsPage";
import { ProtocolDraftEditor } from "../features/protocol/editor/ProtocolDraftEditor";
import { ReportsPage } from "../features/reports/ReportsPage";
import { ComparePage } from "../features/run-comparison/ComparePage";
import { RunHistoryPage } from "../features/run-history/RunHistoryPage";
import { RunPanel } from "../features/runs/RunPanel";
import { SchedulesPage } from "../features/schedules/SchedulesPage";
import { SettingsPage } from "../features/settings/SettingsPage";
import { StateReferencePage } from "../features/state-reference/StateReferencePage";
import { TeamPage } from "../features/team/TeamPage";
import { WorkspaceView } from "../features/workspace/WorkspaceView";
/**
 * 页面注册表（T06）：每条规范路由 → 独立页面组件。
 * 已有真实能力的页面先接入现有面板（T15-T23 重建）；
 * 缺口页使用 GapPage 脚手架呈现页面身份与支持等级（T24-T27 扩面）。
 */

import { Suspense, type ReactNode } from "react";
import { LoadingState } from "../components/States";
import { useI18n } from "../i18n/useI18n";

import type { PageContext } from "./pageContext";
import { pageSupport } from "./pageSupport";
import type { Route } from "./registry";

export type { PageContext };

type PageFactory = (route: Route, ctx: PageContext) => ReactNode;

/** 已接入真实面板的页面（T15-T23 将逐页重建为高保真版本）。 */
const REAL_PAGES: Readonly<Record<string, PageFactory>> = {
  "plan/overview": (_r, ctx) => <OverviewPage ctx={ctx} />,
  "plan/protocol": (_r, ctx) => (
    <ProtocolDraftEditor
      draftId={ctx.selectedDraftId}
      onDraftSaved={ctx.onDraftIdChange}
      onDraftIdChange={ctx.onDraftIdChange}
      onRunStarted={ctx.onSelectedRunIdChange}
    />
  ),
  "plan/team": () => <TeamPage />,
  "library/endpoints": (_r, ctx) => (
    <EndpointsHome
      endpoints={ctx.endpoints}
      onAddRelay={ctx.onAddRelay}
      onChanged={ctx.refreshEndpoints}
    />
  ),
  "library/model-registry": () => <ModelsPage />,
  "run/timeline": (_r, ctx) => (
    <RunPanel onRunSelected={ctx.onSelectedRunIdChange} initialRunId={ctx.selectedRunId} />
  ),
  "run/approvals": () => <ApprovalsPanel />,
  "run/workspace": (_r, ctx) => (
    <WorkspaceView initialRunId={ctx.selectedRunId} onRunSelected={ctx.onSelectedRunIdChange} />
  ),
  "evidence/claims": (_r, ctx) => (
    <InspectionPanel initialRunId={ctx.selectedRunId} onRunSelected={ctx.onSelectedRunIdChange} />
  ),
  "portfolio/compare": () => <ComparePage />,
  "portfolio/experiments": (_r, ctx) => <ExperimentsPage ctx={ctx} />,
  "library/lineage": (_r, ctx) => <LineagePage ctx={ctx} />,
  "insights/cost-analytics": (_r, ctx) => <CostAnalyticsPage ctx={ctx} />,
  "govern/budget": (_r, ctx) => <BudgetPage ctx={ctx} />,
  "settings/settings": (_r, ctx) => (
    <SettingsPage preferences={ctx.preferences} onPreferencesChange={ctx.onPreferencesChange} />
  ),
  "portfolio/projects": () => <ProjectsPage />,
  "portfolio/runs-history": (_r, ctx) => <RunHistoryPage ctx={ctx} />,
  "library/prompts": () => <PromptsPage />,
  "library/datasets": () => <DatasetsPage />,
  "library/notebooks": () => <NotebooksPage />,
  "insights/reports": () => <ReportsPage />,
  "ops/alerts": () => <AlertsPage />,
  "ops/incidents": () => <IncidentsPage />,
  "ops/schedules": () => <SchedulesPage />,
  "ops/integrations": () => <IntegrationsPage />,
  "ops/data-health": () => <DataHealthPage />,
  "ops/matrix": () => <StateReferencePage />,
  "govern/audit": (_r, ctx) => <GovernancePage ctx={ctx} />,
  "notifications/notifications": () => <NotificationsPage />,  "ops/observability": (_r, ctx) => (
    <OperationsPanel initialRunId={ctx.selectedRunId} onRunSelected={ctx.onSelectedRunIdChange} />
  ),
  "ops/compute": (_r, ctx) => <ComputePage runId={ctx.selectedRunId} />,
};

function routeKey(route: Route): string {
  return `${route.domain}/${route.page}`;
}

export function PageRenderer({ route, ctx }: { route: Route; ctx: PageContext }): ReactNode {
  const { t } = useI18n();
  const factory = REAL_PAGES[routeKey(route)];
  return (
    <Suspense fallback={<LoadingState message={t("state.loading")} />}>
      {factory === undefined ? (
        <GapPage route={route} support={pageSupport(route)} />
      ) : (
        factory(route, ctx)
      )}
    </Suspense>
  );
}
