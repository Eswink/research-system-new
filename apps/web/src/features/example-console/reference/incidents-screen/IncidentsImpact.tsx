import visual from "../IncidentsScreen.module.css";
import { Section } from "../Section";
import { IncidentsSection3 } from "./IncidentsSection3";

interface IncidentsImpactProps {
  t: (key: string, fallback?: string) => string;
  selected:
    | {
        id: string;
        title: string;
        severity: string;
        status: string;
        opened_at: string;
        resolved_at: string;
        duration_min: number;
        commander: string;
        scope: string[];
        impact: string;
        rca_cause: string;
        action_items: { id: string; text: string; owner: string; status: string; due: string }[];
        timeline: { at: string; event: string; actor: string }[];
      }
    | {
        id: string;
        title: string;
        severity: string;
        status: string;
        opened_at: string;
        resolved_at: null;
        duration_min: null;
        commander: string;
        scope: string[];
        impact: string;
        rca_cause: null;
        action_items: { id: string; text: string; owner: string; status: string; due: string }[];
        timeline: { at: string; event: string; actor: string }[];
      };
}

export function IncidentsImpact({ t, selected }: IncidentsImpactProps) {
  return (
    <div className={visual.column2}>
      {/* Impact */}
      <Section label={t("ic.impact")}>
        <div className={visual.label4}>{selected.impact}</div>
        <div className={visual.row5}>
          {selected.scope.map((s) => (
            <span key={s} className={`chip mono ${visual.caption5 ?? ""}`}>
              {s}
            </span>
          ))}
        </div>
      </Section>

      {/* Timeline */}
      <Section label={t("ic.timeline")}>
        <div className={visual.column3}>
          <div className={visual.overlay} />
          {selected.timeline.map((ev, i) => (
            <div key={i} className={visual.grid3}>
              <span className={`mono ${visual.caption6 ?? ""}`}>{ev.at}</span>
              <span
                className={visual.surface7}
                style={{
                  background: ev.actor === "system" ? "var(--warn)" : "var(--accent)",
                }}
              />
              <span className={visual.label5}>{ev.event}</span>
              <span className={`mono ${visual.caption7 ?? ""}`}>{ev.actor}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* RCA */}
      <Section label={t("ic.rca")}>
        {selected.rca_cause ? (
          <div className={visual.label6}>{selected.rca_cause}</div>
        ) : (
          <div className={`empty-mark ${visual.row6 ?? ""}`}>{t("ic.rcaPending")}</div>
        )}
      </Section>

      {/* Action items */}
      <IncidentsSection3 {...{ t, selected }} />
    </div>
  );
}
