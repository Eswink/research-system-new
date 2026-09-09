import { Icon } from "../Icon";
import visual from "../IncidentsScreen.module.css";
import { Section } from "../Section";

interface IncidentsSection3Props {
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

export function IncidentsSection3({ t, selected }: IncidentsSection3Props) {
  return (
    <Section
      label={`${t("ic.actionItems")} (${String(
        selected.action_items.filter((a) => a.status === "done").length,
      )}/${String(selected.action_items.length)})`}
    >
      <div className={visual.column4}>
        {selected.action_items.map((a) => {
          const st =
            a.status === "done"
              ? { icon: "check", color: "var(--success)" }
              : a.status === "in-progress"
                ? { icon: "spin", color: "var(--accent)" }
                : { icon: "circle-o", color: "var(--fg-faint)" };
          return (
            <div key={a.id} className={visual.grid4}>
              <Icon name={st.icon} size={12} style={{ color: st.color }} />
              <span
                className={visual.label7}
                style={{
                  textDecoration: a.status === "done" ? "line-through" : "none",
                  color: a.status === "done" ? "var(--fg-muted)" : "var(--fg)",
                }}
              >
                {a.text}
              </span>
              <span className={`mono ${visual.caption8 ?? ""}`}>{a.owner}</span>
              <span
                className={`mono ${visual.caption9 ?? ""}`}
                style={{ color: a.status === "done" ? "var(--fg-faint)" : "var(--warn)" }}
              >
                {a.due}
              </span>
            </div>
          );
        })}
      </div>
    </Section>
  );
}
