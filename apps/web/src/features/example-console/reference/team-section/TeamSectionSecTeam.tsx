import type * as E from "../../exampleTypes";
import { Field } from "../Field";
import { SectionHeader } from "../SectionHeader";
import visual from "../TeamSection.module.css";
import { TeamSectionSection } from "./TeamSectionSection";

interface TeamSectionSecTeamProps {
  t: (key: string, fallback?: string) => string;
  templates: { id: string; label: string; desc: string; roles: number }[];
  value: {
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
  setP: E.UpdateProtocol;
  roleOptions: string[];
}

export function TeamSectionSecTeam({
  t,
  templates,
  value,
  setP,
  roleOptions,
}: TeamSectionSecTeamProps) {
  return (
    <div>
      <SectionHeader title={t("pe.sec.team")} subtitle={t("pe.sec.teamDesc")} />

      <Field label="team.template" tooltip={t("pe.tm.tip.template")}>
        <div className={visual.grid}>
          {templates.map((tm) => {
            const active = value.team.template === tm.id;
            return (
              <button
                key={tm.id}
                onClick={() => {
                  setP((p) => {
                    p.team.template = tm.id;
                  });
                }}
                className={visual.action}
                style={{
                  background: active ? "var(--accent-dim)" : "var(--bg-sunken)",
                  border: `1px solid ${active ? "var(--accent-line)" : "var(--border)"}`,
                }}
              >
                <div
                  className={visual.label}
                  style={{ color: active ? "var(--accent)" : "var(--fg-muted)" }}
                >
                  {tm.label}
                </div>
                <div className={visual.caption}>{tm.desc}</div>
                <div className={visual.caption2}>
                  {tm.roles} {t("pe.tm.roles")}
                </div>
              </button>
            );
          })}
        </div>
      </Field>

      <TeamSectionSection {...{ t, value, setP, roleOptions }} />
    </div>
  );
}
