import type * as E from "../../exampleTypes";
import { BudgetSection } from "../BudgetSection";
import { EvaluationSection } from "../EvaluationSection";
import { GatesSection } from "../GatesSection";
import { ManifestSection } from "../ManifestSection";
import { ObjectivesSection } from "../ObjectivesSection";
import { PolicySection } from "../PolicySection";
import visual from "../ProtocolEditor.module.css";
import { TeamSection } from "../TeamSection";

interface ProtocolEditorSectionProps {
  activeSection: string;
  protocol: {
    protocol_version: string;
    manifest: { id: string; name: string; autonomy_level: string };
    objectives: { id: string; statement: string }[];
    team: {
      template: string;
      overrides: (
        | { role: string; instances: number; collapse_when: string }
        | { role: string; instances: null; collapse_when: string }
      )[];
    };
    evaluation: {
      benchmarks: string[];
      languages: string[];
      n_per_lang: number;
      temperature_grid: number[];
    };
    budget: {
      cap_minor: number;
      hard_stop_on_breach: boolean;
      reservations: { resource: string; minor: number }[];
    };
    gates: { kind: string; at: string }[];
    policy: { heterogeneous_review: string; memory_write: string; redact_prompts: boolean };
  };
  setP: (updater: (draft: E.Protocol) => void) => void;
  errors: E.ProtocolIssue[];
  adminMode: boolean;
  warnings: E.ProtocolIssue[];
}

export function ProtocolEditorSection({
  activeSection,
  protocol,
  setP,
  errors,
  adminMode,
  warnings,
}: ProtocolEditorSectionProps) {
  return (
    <div className={visual.surface}>
      {activeSection === "manifest" && (
        <ManifestSection value={protocol} setP={setP} errors={errors} adminMode={adminMode} />
      )}
      {activeSection === "objectives" && (
        <ObjectivesSection value={protocol} setP={setP} errors={errors} />
      )}
      {activeSection === "team" && <TeamSection value={protocol} setP={setP} errors={errors} />}
      {activeSection === "evaluation" && (
        <EvaluationSection value={protocol} setP={setP} errors={errors} warnings={warnings} />
      )}
      {activeSection === "budget" && (
        <BudgetSection value={protocol} setP={setP} errors={errors} warnings={warnings} />
      )}
      {activeSection === "gates" && <GatesSection value={protocol} setP={setP} errors={errors} />}
      {activeSection === "policy" && (
        <PolicySection value={protocol} setP={setP} adminMode={adminMode} />
      )}
    </div>
  );
}
