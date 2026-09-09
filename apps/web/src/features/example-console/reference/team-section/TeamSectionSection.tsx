import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";
import visual from "../TeamSection.module.css";
import { TooltipIcon } from "../TooltipIcon";
import { TeamSectionSection2 } from "./TeamSectionSection2";

interface TeamSectionSectionProps {
  t: (key: string, fallback?: string) => string;
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

export function TeamSectionSection({ t, value, setP, roleOptions }: TeamSectionSectionProps) {
  return (
    <div className={visual.surface}>
      <div className={visual.row}>
        <label className={visual.label2}>team.overrides</label>
        <TooltipIcon text={t("pe.tm.tip.overrides")} />
        <span className="chip">{value.team.overrides.length}</span>
      </div>

      {/* Table header */}
      <div className={visual.grid2}>
        <span>role</span>
        <span>instances</span>
        <span>collapse_when</span>
        <span />
      </div>
      <TeamSectionSection2 {...{ value, setP, roleOptions }} />
      <button
        className={`btn sm ${visual.action3 ?? ""}`}

        onClick={() => {
          setP((p) => {
            p.team.overrides.push({ role: "role_reviewer", instances: 1, collapse_when: "" });
          });
        }}
      >
        <Icon name="plus" size={10} /> {t("pe.tm.addOverride")}
      </button>
    </div>
  );
}
