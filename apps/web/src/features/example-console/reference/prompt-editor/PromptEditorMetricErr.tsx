import { MetricCard } from "../MetricCard";
import visual from "../PromptEditor.module.css";

interface PromptEditorMetricErrProps {
  t: (key: string, fallback?: string) => string;
}

export function PromptEditorMetricErr({ t }: PromptEditorMetricErrProps) {
  return (
    <MetricCard
      label={t("pr.metricErr")}
      value="0.42%"
      sub={
        <span>
          {t("pr.metricErrSub")}{" "}
          <span className={`mono ${visual.surface9 ?? ""}`}>52 {t("pr.metricErrors")}</span>
        </span>
      }
      bar={0.042}
      barColor="var(--danger)"
    />
  );
}
