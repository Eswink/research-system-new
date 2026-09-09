import { api } from "../../api/client";
import type { BudgetViewDto, RunDetailDto } from "../../api/types";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useResource, type ResourceState } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { ledgerMinorText } from "../budget/ledgerPresentation";
import { ExperimentMetadata } from "../experiments/ExperimentMetadata";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

/** Side-by-side facts, not a locally manufactured comparability decision or ranking. */
export function RunComparisonColumn({ run }: { run: RunDetailDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const usage = useResource(run.id, () => api.runUsage(run.id));
  const experiments = useResource(run.id, () => api.runExperiments(run.id));
  const value = usage.data;
  return (
    <div className={styles.page} data-testid={`compare-run-${run.id}`}>
      <PanelSection title={run.id}>
        <KeyValueList
          fields={[
            { label: "State", value: run.state },
            { label: "Protocol", value: run.protocol_id },
            { label: "Manifest", value: run.manifest_digest ?? "NOT FROZEN" },
            { label: "Created", value: run.created_at },
          ]}
        />
      </PanelSection>
      <RunComparisonColumnResourceBoundary {...{ usage, value, zh }} />
      <ResourceBoundary state={experiments}>
        {experiments.data !== null && (
          <>
            {experiments.data.experiments.length === 0 && (
              <EmptyState message={zh ? "无已记录实验指标" : "No recorded experiment metrics"} />
            )}
            {experiments.data.experiments.map((experiment) => (
              <ExperimentMetadata key={experiment.experiment_run_id} experiment={experiment} />
            ))}
          </>
        )}
      </ResourceBoundary>
    </div>
  );
}

interface RunComparisonColumnResourceBoundaryProps {
  usage: ResourceState<BudgetViewDto>;
  value: BudgetViewDto | null;
  zh: boolean;
}

function RunComparisonColumnResourceBoundary({
  usage,
  value,
  zh,
}: RunComparisonColumnResourceBoundaryProps) {
  return (
    <ResourceBoundary state={usage}>
      {value !== null && (
        <PanelSection title={zh ? "该运行的使用账本" : "This run's usage ledger"}>
          <KeyValueList
            fields={[
              {
                label: zh ? "总估算金额" : "Estimated total",
                value: ledgerMinorText(value.total_estimated_cost_minor, value.total_currency),
              },
              {
                label: zh ? "已知小计" : "Known subtotal",
                value: ledgerMinorText(value.known_cost_subtotal_minor, value.total_currency),
              },
              { label: zh ? "未知条目" : "Unknown entries", value: value.unknown_cost_entries },
            ]}
          />
        </PanelSection>
      )}
    </ResourceBoundary>
  );
}
