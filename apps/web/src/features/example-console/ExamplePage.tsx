import { Suspense, type ReactNode } from "react";
import { LoadingState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import type { Route } from "../../navigation/registry";
import styles from "./ExampleConsole.module.css";
import { InfrastructureExample } from "./InfrastructureExample";
import { AlertsScreen } from "./reference/AlertsScreen";
import { ApprovalsScreen } from "./reference/ApprovalsScreen";
import { BudgetScreen } from "./reference/BudgetScreen";
import { ClaimsScreen } from "./reference/ClaimsScreen";
import { CompareScreen } from "./reference/CompareScreen";
import { CostAnalyticsScreen } from "./reference/CostAnalyticsScreen";
import { DataHealthScreen } from "./reference/DataHealthScreen";
import { DatasetsScreen } from "./reference/DatasetsScreen";
import { DryRunScreen } from "./reference/DryRunScreen";
import { EndpointsScreen } from "./reference/EndpointsScreen";
import { ExperimentsScreen } from "./reference/ExperimentsScreen";
import { GovernScreen } from "./reference/GovernScreen";
import { IncidentsScreen } from "./reference/IncidentsScreen";
import { IntegrationsScreen } from "./reference/IntegrationsScreen";
import { LineageScreen } from "./reference/LineageScreen";
import { ModelRegistryScreen } from "./reference/ModelRegistryScreen";
import { NotebooksScreen } from "./reference/NotebooksScreen";
import { NotificationsScreen } from "./reference/NotificationsScreen";
import { PlanOverview } from "./reference/PlanOverview";
import { ProjectsScreen } from "./reference/ProjectsScreen";
import { PromptsScreen } from "./reference/PromptsScreen";
import { ReportsScreen } from "./reference/ReportsScreen";
import { RunsHistoryScreen } from "./reference/RunsHistoryScreen";
import { SchedulesScreen } from "./reference/SchedulesScreen";
import { SettingsScreen } from "./reference/SettingsScreen";
import { SetupScreen } from "./reference/SetupScreen";
import { StatesScreen } from "./reference/StatesScreen";
import { TeamScreen } from "./reference/TeamScreen";
import { TimelineScreen } from "./reference/TimelineScreen";
import { WorkspaceScreen } from "./reference/WorkspaceScreen";

/** Native routes from the frozen handoff; never imports a real API client. */
const PAGES: Readonly<Record<string, () => ReactNode>> = {
  "plan/overview": () => <PlanOverview />,
  "plan/protocol": () => <DryRunScreen preflightState="warn" />,
  "plan/team": () => <TeamScreen />,
  "portfolio/projects": () => <ProjectsScreen />,
  "portfolio/experiments": () => <ExperimentsScreen />,
  "portfolio/runs-history": () => <RunsHistoryScreen />,
  "portfolio/compare": () => <CompareScreen />,
  "run/timeline": () => <TimelineScreen />,
  "run/approvals": () => <ApprovalsScreen />,
  "run/workspace": () => <WorkspaceScreen />,
  "library/prompts": () => <PromptsScreen />,
  "library/datasets": () => <DatasetsScreen />,
  "library/notebooks": () => <NotebooksScreen />,
  "library/model-registry": () => <ModelRegistryScreen />,
  "library/lineage": () => <LineageScreen />,
  "library/endpoints": () => <EndpointsScreen />,
  "library/setup": () => <SetupScreen />,
  "evidence/claims": () => <ClaimsScreen initialView="graph" />,
  "insights/reports": () => <ReportsScreen />,
  "insights/cost-analytics": () => <CostAnalyticsScreen />,
  "ops/alerts": () => <AlertsScreen />,
  "ops/incidents": () => <IncidentsScreen />,
  "ops/schedules": () => <SchedulesScreen />,
  "ops/integrations": () => <IntegrationsScreen />,
  "ops/data-health": () => <DataHealthScreen />,
  "ops/matrix": () => <StatesScreen />,
  "govern/budget": () => <BudgetScreen />,
  "govern/audit": () => <GovernScreen />,
  "settings/settings": () => <SettingsScreen />,
  "notifications/notifications": () => <NotificationsScreen />,
  "ops/compute": () => <InfrastructureExample kind="compute" />,
  "ops/observability": () => <InfrastructureExample kind="observability" />,
};

export function ExamplePage({ route }: { route: Route }) {
  const { t } = useI18n();
  const factory = PAGES[`${route.domain}/${route.page}`];
  if (factory === undefined) return <div role="alert">Missing example route</div>;
  return (
    <Suspense fallback={<LoadingState message={t("state.loading")} />}>
      <div className={styles.loaded} data-example-loaded={`${route.domain}/${route.page}`}>
        {factory()}
      </div>
    </Suspense>
  );
}
