import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import { ReproducibilityChip } from "./ReproducibilityChip";
import visual from "./StepProbe.module.css";

/** Reference: screens/Setup.jsx; EXAMPLE ONLY. */
export const StepProbe = () => {
  const { t } = useI18n();
  const rows = [
    {
      model: "claude-opus-4-1-20250805",
      status: "ok",
      caps: [
        ["chat", "ok"],
        ["tool_calls", "ok"],
        ["extended_thinking", "ok"],
      ],
      fpAvail: false,
    },
    {
      model: "claude-sonnet-4-20250514",
      status: "ok",
      caps: [
        ["chat", "ok"],
        ["tool_calls", "ok"],
        ["json_mode", "degraded"],
        ["vision", "ok"],
      ],
      fpAvail: false,
    },
    { model: "claude-3-5-haiku-20241022", status: "probing", caps: [], fpAvail: null },
  ];
  return <StepProbeSection {...{ t, rows }} />;
};

interface StepProbeSectionProps {
  t: (key: string, fallback?: string) => string;
  rows: (
    | { model: string; status: string; caps: string[][]; fpAvail: boolean }
    | { model: string; status: string; caps: never[]; fpAvail: null }
  )[];
}

function StepProbeSection({ t, rows }: StepProbeSectionProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <div>
          <div className={visual.label}>{t("st.probe.title")}</div>
          <div className={visual.label2}>{t("st.probe.desc")}</div>
        </div>
        <div className={visual.label3}>2/3 {t("st.probe.done")}</div>
      </div>
      <StepProbeSection2 {...{ rows, t }} />
    </div>
  );
}

interface StepProbeSection2Props {
  rows: (
    | { model: string; status: string; caps: string[][]; fpAvail: boolean }
    | { model: string; status: string; caps: never[]; fpAvail: null }
  )[];
  t: (key: string, fallback?: string) => string;
}

function StepProbeSection2({ rows, t }: StepProbeSection2Props) {
  return (
    <div className={visual.surface}>
      {rows.map((r, i) => (
        <div
          key={r.model}
          className={visual.surface2}
          style={{
            borderBottom: i < rows.length - 1 ? "1px solid var(--border-subtle)" : "none",
            background: r.status === "probing" ? "var(--bg-raised)" : "transparent",
          }}
        >
          <div className={visual.row2}>
            {r.status === "probing" ? (
              <Icon name="spin" size={12} className={visual.surface3} />
            ) : (
              <Icon name="check" size={12} className={visual.surface4} />
            )}
            <span className={`mono ${visual.label4 ?? ""}`}>{r.model}</span>
            {r.status === "probing" && (
              <span className={visual.caption}>{t("st.probe.probing")}</span>
            )}
            {r.status !== "probing" && r.fpAvail === false && (
              <ReproducibilityChip fingerprint={null} providerAvailable={false} compact={true} />
            )}
          </div>
          {r.caps.length > 0 && (
            <div className={visual.row3}>
              {r.caps.map(([cap, st]) => (
                <span
                  key={cap}
                  className={visual.row4}
                  style={{
                    background: st === "degraded" ? "var(--warn-dim)" : "var(--success-dim)",
                    border: `1px solid ${
                      st === "degraded" ? "var(--warn-line)" : "var(--success-line)"
                    }`,
                    color: st === "degraded" ? "var(--warn)" : "var(--success)",
                  }}
                >
                  <Icon name={st === "degraded" ? "warn-tri" : "check"} size={9} /> {cap}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
