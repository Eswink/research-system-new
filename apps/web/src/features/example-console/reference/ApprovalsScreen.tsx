import { useState } from "react";
import FIX_APPROVALS from "../data/approvals.json";
import { requiredExample } from "../requiredExample";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./ApprovalsScreen.module.css";
import { ApprovalsSection } from "./approvals-screen/ApprovalsSection";
import { ApprovalsSection4 } from "./approvals-screen/ApprovalsSection4";

export const ApprovalsScreen = () => {
  const { t } = useI18n();
  // Default to the high-risk model replacement so the consequence panel is visible.
  const [selectedId, setSelectedId] = useState(requiredExample(FIX_APPROVALS[1]).id);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [processed, setProcessed] = useState<Record<string, string>>({});

  const pending = FIX_APPROVALS.filter((a) => !processed[a.id]);
  const selected = FIX_APPROVALS.find((a) => a.id === selectedId);
  const riskOrder: Record<string, number> = { high: 0, medium: 1, low: 2 };
  const sorted = [...pending].sort((a, b) => (riskOrder[a.risk] ?? 0) - (riskOrder[b.risk] ?? 0));

  return (
    <div className={visual.grid}>
      {/* Queue */}
      <ApprovalsSection4
        {...{ t, sorted, selectedId, expanded, setSelectedId, setExpanded, setProcessed }}
      />

      {/* Detail rail */}
      <ApprovalsSection {...{ t, selected }} />
    </div>
  );
};
