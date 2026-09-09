import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { GATE_KINDS } from "./gateKinds";
import visual from "./GatesSection.module.css";
import { Icon } from "./Icon";
import { INPUT_MONO } from "./inputMono";
import { SectionHeader } from "./SectionHeader";

/** Reference: screens/ProtocolEditor.sections.jsx; EXAMPLE ONLY. */
export const GatesSection = ({ value, setP }: E.ProtocolSectionProps) => {
  const { t } = useI18n();
  const kindHints: Record<string, string> = {
    BUDGET_GATE: t("pe.gt.bd"),
    QUALITY_GATE: t("pe.gt.qa"),
    PUBLISH_GATE: t("pe.gt.pub"),
    SECURITY_GATE: t("pe.gt.sec"),
    ETHICS_GATE: t("pe.gt.eth"),
  };
  const kindTones: Record<string, string> = {
    BUDGET_GATE: "warn",
    QUALITY_GATE: "accent",
    PUBLISH_GATE: "unknown",
    SECURITY_GATE: "danger",
    ETHICS_GATE: "danger",
  };
  return <GatesSectionSecGates {...{ t, value, kindTones, setP, kindHints }} />;
};

interface GatesSectionSecGatesProps {
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
  kindTones: Record<string, string>;
  setP: E.UpdateProtocol;
  kindHints: Record<string, string>;
}

function GatesSectionSecGates({ t, value, kindTones, setP, kindHints }: GatesSectionSecGatesProps) {
  return (
    <div>
      <SectionHeader
        title={t("pe.sec.gates")}
        subtitle={t("pe.sec.gatesDesc")}
        extra={
          <span className="chip">
            {value.gates.length} · {t("pe.gt.total")}
          </span>
        }
      />

      {value.gates.map((g, i) => {
        const tone = kindTones[g.kind] ?? "neutral";
        return (
          <div key={i} className={visual.surface}>
            <GatesSectionSection {...{ g, setP, i, tone }} />
            <div className={visual.caption}>{kindHints[g.kind]}</div>
          </div>
        );
      })}
      <button
        className={`btn ${visual.action2 ?? ""}`}
        onClick={() => {
          setP((p) => {
            p.gates.push({ kind: "QUALITY_GATE", at: "" });
          });
        }}
      >
        <Icon name="plus" size={11} /> {t("pe.gt.add")}
      </button>
    </div>
  );
}

interface GatesSectionSectionProps {
  g: { kind: string; at: string };
  setP: E.UpdateProtocol;
  i: number;
  tone: string;
}

function GatesSectionSection({ g, setP, i, tone }: GatesSectionSectionProps) {
  return (
    <div className={visual.grid}>
      <GatesSectionselect {...{ g, setP, i, tone }} />
      <input
        value={g.at}
        onChange={(e) => {
          setP((p) => {
            const row = p.gates[i];
            if (row) row.at = e.target.value;
          });
        }}
        placeholder="trigger condition …"
        style={{ ...INPUT_MONO, minWidth: 0 }}
      />
      <button
        className={`btn sm ghost ${visual.action ?? ""}`}
        onClick={() => {
          setP((p) => {
            p.gates.splice(i, 1);
          });
        }}
      >
        <Icon name="x" size={9} />
      </button>
    </div>
  );
}

interface GatesSectionselectProps {
  g: { kind: string; at: string };
  setP: E.UpdateProtocol;
  i: number;
  tone: string;
}

function GatesSectionselect({ g, setP, i, tone }: GatesSectionselectProps) {
  return (
    <select
      value={g.kind}
      onChange={(e) => {
        setP((p) => {
          const row = p.gates[i];
          if (row) row.kind = e.target.value;
        });
      }}
      style={{
        ...INPUT_MONO,
        width: "100%",
        minWidth: 0,
        fontSize: 11,
        background: `var(--${tone}-dim)`,
        borderColor: `var(--${tone}-line)`,
        color: `var(--${tone})`,
        fontWeight: 500,
        letterSpacing: "0.04em",
      }}
    >
      {GATE_KINDS.map((k) => (
        <option key={k} value={k}>
          {k}
        </option>
      ))}
    </select>
  );
}
