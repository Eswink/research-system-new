import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";
import visual from "../IncidentsScreen.module.css";
import { StatusBadge } from "../StatusBadge";

interface IncidentsSection7Props {
  sev: { color: string; label: string; icon?: string };
  st: E.BadgeProps;
  inc:
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

export function IncidentsSection7({ sev, st, inc }: IncidentsSection7Props) {
  return (
    <div className={visual.row}>
      <Icon name={sev.icon} size={12} style={{ color: sev.color }} />
      <span className={`mono ${visual.caption ?? ""}`} style={{ color: sev.color }}>
        {sev.label}
      </span>
      <StatusBadge tone={st.tone} icon={st.icon} label={st.label} filled={st.filled} size="sm" />
      <span className={`mono ${visual.caption2 ?? ""}`}>{inc.id}</span>
    </div>
  );
}
