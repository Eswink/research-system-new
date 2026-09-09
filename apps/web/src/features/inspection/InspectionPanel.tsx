import type { BudgetViewDto, ClaimMapDto, EvidenceDto } from "../../api/types";
import { api } from "../../api/client";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useResource, type ResourceState } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";
import { useSelectedRun, type RunSelectionProps } from "../shared/useSelectedRun";
import { ClaimsWorkspace } from "./ClaimsWorkspace";
import { UsageView } from "./Views";

/** Selection is local; verification and status transitions are exclusively backend-owned. */
export function InspectionPanel(props: RunSelectionProps = {}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const { runId, selectRun } = useSelectedRun(props);
  const key = runId === "" ? null : runId;
  const claims = useResource(key, () => api.runClaimMap(runId));
  const evidence = useResource(key, () => api.runEvidence(runId));
  const usage = useResource(key, () => api.runUsage(runId));
  return (
    <section className={styles.page} data-testid="inspection-panel">
      <InspectionPanelPageHeader {...{ zh, runId, claims, evidence, usage, selectRun }} />
      {runId === "" && (
        <EmptyState
          message={zh ? "选择运行以检查研究证据" : "Select a run to inspect research evidence"}
        />
      )}
      <ResourceBoundary state={claims}>
        {claims.data !== null && (
          <ClaimsWorkspace
            key={runId}
            claims={claims.data}
            evidence={evidence.phase === "ready" ? evidence.data : null}
          />
        )}
      </ResourceBoundary>
      <ResourceBoundary state={evidence}>{null}</ResourceBoundary>
      <ResourceBoundary state={usage}>
        {usage.data !== null && <UsageView usage={usage.data} />}
      </ResourceBoundary>
    </section>
  );
}

interface InspectionPanelPageHeaderProps {
  zh: boolean;
  runId: string;
  claims: ResourceState<ClaimMapDto>;
  evidence: ResourceState<EvidenceDto[]>;
  usage: ResourceState<BudgetViewDto>;
  selectRun: (value: string) => void;
}

function InspectionPanelPageHeader({
  zh,
  runId,
  claims,
  evidence,
  usage,
  selectRun,
}: InspectionPanelPageHeaderProps) {
  return (
    <PageHeader
      title={zh ? "论断与证据" : "Claims and evidence"}
      kicker="EVIDENCE / CLAIM MAP"
      description={
        zh
          ? "正式 Claim / Evidence / Relation 投影，保留争议、无支持与降级状态。"
          : [
              "Persisted claims, evidence and relations, including disputes, ",
              "unsupported claims and degraded projections.",
            ].join("")
      }
      actions={
        <RunQueryBar
          runId={runId}
          onSelect={(id) => {
            if (id === runId) {
              claims.reload();
              evidence.reload();
              usage.reload();
            } else selectRun(id);
          }}
          busy={claims.phase === "loading"}
        />
      }
    />
  );
}
