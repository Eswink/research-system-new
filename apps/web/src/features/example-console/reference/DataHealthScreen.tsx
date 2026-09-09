import { useState } from "react";
import { requiredExample } from "../requiredExample";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { DataHealthTitle } from "./data-health-screen/DataHealthTitle";
import { DH_METRICS } from "./dhMetrics";

export const DataHealthScreen = () => {
  const { t } = useI18n();
  // Start with the Arabic metric because it demonstrates a non-healthy state.
  const [selectedId, setSelectedId] = useState(requiredExample(DH_METRICS[2]).id);

  const selected = DH_METRICS.find((d) => d.id === selectedId);
  const health = (m: (typeof DH_METRICS)[number]) => {
    let issues = 0;
    if (m.drift > 0.15) issues++;
    if (m.freshness_d > 10) issues++;
    if (m.pii_hits > 0) issues++;
    if (m.label_skew > 0.35) issues++;
    if (!m.schema_ok) issues++;
    if (issues === 0) return { tone: "success", label: "HEALTHY", icon: "check" };
    if (issues <= 2) return { tone: "warn", label: "DEGRADED", icon: "warn-tri" };
    return { tone: "danger", label: "UNHEALTHY", icon: "x" };
  };

  return <DataHealthTitle {...{ t, health, selectedId, setSelectedId, selected }} />;
};
