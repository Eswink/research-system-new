import { type Dispatch, type SetStateAction } from "react";
import visual from "../TeamScreen.module.css";
import { TeamSection3 } from "./TeamSection3";

interface TeamSection2Props {
  t: (key: string, fallback?: string) => string;
  templates: { id: string; label: string; roles: number; desc: string; agents: string }[];
  setTemplate: Dispatch<SetStateAction<string>>;
  template: string;
  modelUsage: Record<string, string[]>;
  setSelectedAgent: Dispatch<SetStateAction<string | null>>;
  selectedAgent: string | null;
}

export function TeamSection2({
  t,
  templates,
  setTemplate,
  template,
  modelUsage,
  setSelectedAgent,
  selectedAgent,
}: TeamSection2Props) {
  return (
    <div className={visual.column}>
      {/* Template selector */}
      <div className={`panel ${visual.panel ?? ""}`}>
        <div className={visual.caption}>{t("tm.template")}</div>
        <div className={visual.grid}>
          {templates.map((tt) => (
            <div
              key={tt.id}
              onClick={() => {
                setTemplate(tt.id);
              }}
              className={visual.surface}
              style={{
                background: template === tt.id ? "var(--accent-dim)" : "var(--bg-raised)",
                border: `1px solid ${template === tt.id ? "var(--accent)" : "var(--border)"}`,
              }}
            >
              <div className={visual.row}>
                <span
                  className={`mono ${visual.label ?? ""}`}
                  style={{ color: template === tt.id ? "var(--accent)" : "var(--fg)" }}
                >
                  {tt.label}
                </span>
                <span className="chip">
                  {tt.roles} {t("tm.tmplRoles")} · {tt.agents} {t("tm.tmplAgents")}
                </span>
              </div>
              <div className={visual.label2}>{tt.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Roles + Agent grid */}
      <TeamSection3 {...{ t, modelUsage, setSelectedAgent, selectedAgent }} />
    </div>
  );
}
