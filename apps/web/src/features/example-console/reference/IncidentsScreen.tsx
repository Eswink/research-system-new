import { useState } from "react";
import type * as E from "../exampleTypes";
import { requiredExample } from "../requiredExample";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { INCIDENTS } from "./incidents";
import { IncidentsTitle } from "./incidents-screen/IncidentsTitle";

export const IncidentsScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState(requiredExample(INCIDENTS[0]).id);
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered =
    statusFilter === "all" ? INCIDENTS : INCIDENTS.filter((i) => i.status === statusFilter);
  const selected = INCIDENTS.find((i) => i.id === selectedId);

  const sevMap: Record<string, { color: string; label: string; icon?: string }> = {
    sev1: { color: "var(--danger)", label: "SEV1", icon: "warn-tri" },
    sev2: { color: "var(--warn)", label: "SEV2", icon: "warn-tri" },
    sev3: { color: "var(--fg-muted)", label: "SEV3", icon: "diamond" },
    sev4: { color: "var(--fg-faint)", label: "SEV4", icon: "circle-o" },
  };
  const stMap: Record<string, E.BadgeProps> = {
    open: { tone: "danger", icon: "warn-tri", label: "OPEN" },
    postmortem: { tone: "warn", icon: "clock", label: "POSTMORTEM" },
    resolved: { tone: "success", icon: "check", label: "RESOLVED", filled: true },
  };

  return (
    <IncidentsTitle
      {...{
        t,
        statusFilter,
        setStatusFilter,
        filtered,
        selectedId,
        sevMap,
        stMap,
        setSelectedId,
        selected,
      }}
    />
  );
};
