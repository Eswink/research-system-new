import { api } from "../../api/client";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";
import { useSelectedRun, type RunSelectionProps } from "../shared/useSelectedRun";
import { CostView } from "./CostView";
import { EvaluationQuery } from "./EvaluationQuery";
import { TelemetryView } from "./TelemetryView";

/** Telemetry, cost ledger and evaluations remain independent queries and failure boundaries. */
export function OperationsPanel(props: RunSelectionProps = {}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const { runId, selectRun } = useSelectedRun(props);
  const key = runId === "" ? null : runId;
  const telemetry = useResource(key, () => api.runTelemetry(runId));
  const cost = useResource(key, () => api.runCost(runId));
  return (
    <section className={styles.page} data-testid="operations-panel">
      <PageHeader
        title={zh ? "可观测性与评测" : "Observability and evaluation"}
        kicker="OPERATIONS / OBSERVABILITY"
        description={
          zh
            ? "遥测、使用账本和 Evaluation 各自保留来源与错误边界；不采集完整 Prompt 或模型内容。"
            : [
                "Telemetry, usage ledger and evaluation retain separate provenance and ",
                "failure boundaries; no full prompts or model content are collected.",
              ].join("")
        }
        actions={
          <RunQueryBar
            runId={runId}
            onSelect={(id) => {
              if (id === runId) {
                telemetry.reload();
                cost.reload();
              } else selectRun(id);
            }}
            busy={telemetry.phase === "loading" || cost.phase === "loading"}
          />
        }
      />
      {runId === "" && (
        <EmptyState
          message={
            zh ? "选择运行以读取 Telemetry 与 Cost" : "Select a run to load Telemetry & Cost"
          }
        />
      )}
      <ResourceBoundary state={telemetry}>
        {telemetry.data !== null && <TelemetryView telemetry={telemetry.data} />}
      </ResourceBoundary>
      <ResourceBoundary state={cost}>
        {cost.data !== null && <CostView cost={cost.data} />}
      </ResourceBoundary>
      <EvaluationQuery />
    </section>
  );
}
