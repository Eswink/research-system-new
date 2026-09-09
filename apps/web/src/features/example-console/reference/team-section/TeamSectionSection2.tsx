import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";
import { INPUT_MONO } from "../inputMono";
import visual from "../TeamSection.module.css";
import { TeamSectioninput } from "./TeamSectioninput";
import { TeamSectionselect } from "./TeamSectionselect";

interface TeamSectionSection2Props {
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

export function TeamSectionSection2({ value, setP, roleOptions }: TeamSectionSection2Props) {
  return (
    <div className={visual.surface2}>
      {value.team.overrides.map((ov, i) => (
        <div
          key={i}
          className={visual.grid3}
          style={{
            borderBottom:
              i < value.team.overrides.length - 1 ? "1px solid var(--border-subtle)" : "none",
          }}
        >
          <TeamSectionselect {...{ ov, setP, i, roleOptions }} />
          <TeamSectioninput {...{ ov, setP, i }} />
          <input
            value={ov.collapse_when}
            onChange={(e) => {
              setP((p) => {
                const row = p.team.overrides[i];
                if (row) row.collapse_when = e.target.value;
              });
            }}
            placeholder="condition expression …"
            style={INPUT_MONO}
          />
          <button
            className={`btn sm ghost ${visual.action2 ?? ""}`}
            onClick={() => {
              setP((p) => {
                p.team.overrides.splice(i, 1);
              });
            }}
          >
            <Icon name="x" size={9} />
          </button>
        </div>
      ))}
    </div>
  );
}
