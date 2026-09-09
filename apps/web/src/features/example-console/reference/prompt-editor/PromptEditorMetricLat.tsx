import type * as FixtureTypes from "../../fixtureTypes";
import { MetricCard } from "../MetricCard";

interface PromptEditorMetricLatProps {
  t: (key: string, fallback?: string) => string;
  prompt: FixtureTypes.Prompt;
}

export function PromptEditorMetricLat({ t, prompt }: PromptEditorMetricLatProps) {
  return (
    <MetricCard
      label={t("pr.metricLat")}
      value={prompt.avg_latency_ms ? `${String(prompt.avg_latency_ms)}ms` : "—"}
      sub={
        <span>
          {t("pr.metricLatP")}{" "}
          {prompt.avg_latency_ms ? Math.round(prompt.avg_latency_ms * 1.8) : "—"}ms
        </span>
      }
      spark={[8, 7, 9, 8, 7, 8, 7]}
      sparkColor="var(--warn)"
    />
  );
}
