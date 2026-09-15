import { api } from "../../api/client";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import { ClaimsWorkspace } from "../inspection/ClaimsWorkspace";
import { LineageProjection } from "./LineageProjection";
import { ProjectLineagePanel } from "./ProjectLineagePanel";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";

export function LineagePage({ ctx }: { ctx: PageContext }) {
  return (
    <section className={styles.page} data-testid="lineage-page">
      <RunScope ctx={ctx} />
      <ProjectScope />
    </section>
  );
}

/** Run 级投影：选中 run 的 claims/evidence/lineage（未选 run 时给出选择提示）。 */
function RunScope({ ctx }: { ctx: PageContext }) {
  const zh = useI18n().language === "zh";
  const runId = ctx.selectedRunId;
  const key = runId === "" ? null : runId;
  const claims = useResource(key, () => api.runClaimMap(runId));
  const evidence = useResource(key, () => api.runEvidence(runId));
  const lineage = useResource(key, () => api.runLineage(runId));
  return (
    <>
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
    </>
  );
}

/** 项目级合并图（G9）：项目内所有 run 的共享来源/制品/模型 + 未连边库资源。 */
function ProjectScope() {
  const projectLineage = useResource("project-lineage", () => api.projectLineage());
  return (
    <ResourceBoundary state={projectLineage}>
      {projectLineage.data !== null && <ProjectLineagePanel data={projectLineage.data} />}
    </ResourceBoundary>
  );
}

function lineageDescription(zh: boolean): string {
  if (zh) {
    return [
      "当前 Run 的显式来源关系（source→evidence→claim→artifact/model），由后端 persisted 引用构造；",
      "下方项目级合并图展示项目内所有 Run 的共享来源/制品/模型（共享节点即跨 Run 关系）。",
      "数据集/提示词只有未连边清单：资源与 Run 的引用关系无记录面，不猜测连边。",
    ].join("");
  }
  return [
    "Explicit provenance for the selected run (source→evidence→claim→artifact/model), ",
    "projected from persisted references. The project merge below shows sources/artifacts/",
    "models shared across runs (a shared node IS the cross-run relation). Dataset/prompt ",
    "resources are listed unlinked: their run references are not recorded, so none are inferred.",
  ].join("");
}
