import { api } from "../../api/client";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import { ClaimsWorkspace } from "../inspection/ClaimsWorkspace";
import { LineageProjection } from "./LineageProjection";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";

export function LineagePage({ ctx }: { ctx: PageContext }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const runId = ctx.selectedRunId;
  const key = runId === "" ? null : runId;
  const claims = useResource(key, () => api.runClaimMap(runId));
  const evidence = useResource(key, () => api.runEvidence(runId));
  const lineage = useResource(key, () => api.runLineage(runId));
  return (
    <section className={styles.page} data-testid="lineage-page">
      <PageHeader
        title={zh ? "来源血缘" : "Provenance lineage"}
        kicker="LIBRARY / LINEAGE"
        description={lineageDescription(zh)}
        actions={
          <RunQueryBar
            runId={runId}
            onSelect={(id) => {
              if (id === runId) {
                claims.reload();
                evidence.reload();
                lineage.reload();
              } else ctx.onSelectedRunIdChange(id);
            }}
            busy={claims.phase === "loading"}
          />
        }
      />
      {runId === "" && (
        <EmptyState message={zh ? "选择运行以检查血缘" : "Select a run to inspect lineage"} />
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
      {runId !== "" && (
        <ResourceBoundary state={lineage}>
          {lineage.data !== null && <LineageProjection data={lineage.data} />}
        </ResourceBoundary>
      )}
    </section>
  );
}

function lineageDescription(zh: boolean): string {
  if (zh) {
    return [
      "当前 Run 的显式来源关系（source→evidence→claim→artifact/model），",
      "由后端 persisted 引用构造。全局跨 Run 血缘无 API，不猜测。",
    ].join("");
  }
  return [
    "Explicit provenance for the selected run (source→evidence→claim→artifact/model), ",
    "projected from persisted references. Global lineage is unavailable; ",
    "cross-run dependencies are not inferred.",
  ].join("");
}
