import type { ExperimentRunDto } from "../../api/types";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

/** Shared persisted experiment projection for the experiment catalog and workspace. */
export function ExperimentMetadata({ experiment }: { experiment: ExperimentRunDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <div className={styles.page}>
      <PanelSection title={zh ? "元数据预览" : "Metadata preview"}>
        <KeyValueList
          fields={[
            { label: "Experiment", value: experiment.experiment_run_id },
            { label: "Image digest", value: experiment.image_digest ?? "—" },
            { label: "Environment", value: experiment.environment_digest ?? "—" },
            {
              label: "Artifacts",
              value: experiment.artifact_ids.length > 0 ? experiment.artifact_ids.join("\n") : "—",
            },
            {
              label: zh
                ? "复现能力声明（非验收结果）"
                : "Reported reproduction capability (not a test result)",
              value: String(experiment.reproduction_available),
            },
          ]}
        />
      </PanelSection>
      <PanelSection
        title={zh ? "实验指标 · 原始投影" : "Experiment metrics · persisted projection"}
      >
        {Object.keys(experiment.metrics).length === 0 ? (
          <EmptyState message={zh ? "没有已记录指标" : "No recorded metrics"} />
        ) : (
          <pre className={styles.code}>{JSON.stringify(experiment.metrics, null, 2)}</pre>
        )}
      </PanelSection>
    </div>
  );
}
