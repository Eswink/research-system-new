import type * as E from "../../exampleTypes";
import visual from "../IncidentsScreen.module.css";
import { StatusBadge } from "../StatusBadge";

interface IncidentsSection6Props {
  stMap: Record<string, E.BadgeProps>;
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
  sevMap: Record<string, { color: string; label: string; icon?: string }>;
}

export function IncidentsSection6({ stMap, selected, sevMap }: IncidentsSection6Props) {
  return (
    <div className={visual.row3}>
      <StatusBadge
        tone={(stMap[selected.status] ?? { tone: "unknown", label: selected.status }).tone}
        icon={(stMap[selected.status] ?? { tone: "unknown", label: selected.status }).icon}
        label={(stMap[selected.status] ?? { tone: "unknown", label: selected.status }).label}
        filled={(stMap[selected.status] ?? { tone: "unknown", label: selected.status }).filled}
      />
      <span
        className={`mono ${visual.caption3 ?? ""}`}
        style={{
          color: (
            sevMap[selected.severity] ?? {
              color: "var(--unknown)",
              label: selected.severity,
            }
          ).color,
        }}
      >
        {
          (
            sevMap[selected.severity] ?? {
              color: "var(--unknown)",
              label: selected.severity,
            }
          ).label
        }
      </span>
      <span className={`mono ${visual.caption4 ?? ""}`}>{selected.id}</span>
    </div>
  );
}
