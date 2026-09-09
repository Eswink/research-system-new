import { useState } from "react";
import FIX_AGENTS from "../data/agents.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { TeamSection2 } from "./team-screen/TeamSection2";

export const TeamScreen = () => {
  const { t } = useI18n();
  const [template, setTemplate] = useState("STANDARD");
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // Identify heterogeneity conflicts — agents sharing same model_id
  const modelUsage: Record<string, string[]> = {};
  FIX_AGENTS.forEach((a) => {
    const mid = a.model_binding.model_id ?? a.resolved_model_id ?? "unbound";
    (modelUsage[mid] ??= []).push(a.id);
  });

  const templates = [
    { id: "LEAN", label: "LEAN", roles: 5, desc: t("tm.tmpl.lean.desc"), agents: "5-7" },
    { id: "STANDARD", label: "STANDARD", roles: 8, desc: t("tm.tmpl.std.desc"), agents: "10-14" },
    { id: "RIGOROUS", label: "RIGOROUS", roles: 12, desc: t("tm.tmpl.rig.desc"), agents: "16-24" },
  ];

  return (
    <TeamSection2
      {...{ t, templates, setTemplate, template, modelUsage, setSelectedAgent, selectedAgent }}
    />
  );
};
