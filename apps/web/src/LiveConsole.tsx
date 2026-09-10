import { Button } from "./components/Button";
import { CommandCenterPage } from "./features/command-center/CommandCenterPage";
import { RelayWizard } from "./features/setup/RelayWizard";
import { useEndpoints } from "./hooks/useEndpoints";
import { useI18n } from "./i18n/useI18n";
import { ConsoleFrame } from "./layout/ConsoleFrame";
import type { ConsoleProps } from "./layout/consoleProps";
import { LiveEndpointState } from "./layout/LiveEndpointState";
import { isFirstVisitRoute, needsEndpointList } from "./navigation/liveRoutePolicy";
import type { PageContext } from "./navigation/pageContext";
import { PageRenderer } from "./navigation/PageRenderer";
import { DEFAULT_ROUTE } from "./navigation/registry";

/** Only live routes mount API hooks. Unrelated queries cannot gate the entire console. */
export function LiveConsole(props: ConsoleProps) {
  const { resolved, navigate } = props;
  const { route, context: urlContext } = resolved;
  const endpoints = useEndpoints(needsEndpointList(route, urlContext.runId));
  const leaveSetup = () => {
    navigate(DEFAULT_ROUTE, urlContext);
  };
  const openSetup = () => {
    navigate({ domain: "library", page: "setup" }, urlContext);
  };
  const context = createPageContext({ props, endpoints: endpoints.endpoints, openSetup });
  if (route.domain === "command-center") {
    return (
      <CommandCenterPage
        onExit={leaveSetup}
        runId={urlContext.runId}
        onRunSelected={context.onSelectedRunIdChange}
      />
    );
  }
  const explicitSetup = route.domain === "library" && route.page === "setup";
  const firstVisit =
    isFirstVisitRoute(route, urlContext.runId) &&
    endpoints.error === null &&
    endpoints.endpoints.length === 0;
  return (
    <ConsoleFrame {...props}>
      <LiveEndpointState state={endpoints}>
        {explicitSetup || firstVisit ? (
          <LiveWizard onComplete={leaveSetup} onCancel={leaveSetup} canCancel={explicitSetup} />
        ) : (
          <PageRenderer route={route} ctx={context} />
        )}
      </LiveEndpointState>
    </ConsoleFrame>
  );
}

interface PageContextInput {
  props: ConsoleProps;
  endpoints: PageContext["endpoints"];
  openSetup: () => void;
}

function createPageContext({ props, endpoints, openSetup }: PageContextInput): PageContext {
  const { resolved, navigate, preferences, onPreferencesChange } = props;
  const { route, context } = resolved;
  return {
    endpoints,
    preferences,
    onPreferencesChange,
    selectedRunId: context.runId,
    selectedDraftId: context.draftId,
    onDraftIdChange: (draftId) => {
      navigate(route, { ...context, draftId });
    },
    onAddRelay: openSetup,
    onOpenSetup: openSetup,
    onSelectedRunIdChange: (runId) => {
      navigate(route, { ...context, runId });
    },
  };
}

function LiveWizard(props: { canCancel: boolean; onComplete: () => void; onCancel: () => void }) {
  const { t } = useI18n();
  return (
    <div>
      {props.canCancel && (
        <Button variant="ghost" size="sm" data-testid="wizard-cancel" onClick={props.onCancel}>
          {t("setup.cancel")}
        </Button>
      )}
      <RelayWizard onComplete={props.onComplete} />
    </div>
  );
}
