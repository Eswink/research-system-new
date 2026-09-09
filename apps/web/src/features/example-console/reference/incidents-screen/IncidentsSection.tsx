import type * as E from "../../exampleTypes";
import visual from "../IncidentsScreen.module.css";
import { IncidentsSection6 } from "./IncidentsSection6";

interface IncidentsSectionProps {
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
  t: (key: string, fallback?: string) => string;
}

export function IncidentsSection({ stMap, selected, sevMap, t }: IncidentsSectionProps) {
  return (
    <div className={visual.surface3}>
      <IncidentsSection6 {...{ stMap, selected, sevMap }} />
      <div className={visual.label3}>{selected.title}</div>
      <div className={visual.row4}>
        <span>
          <span className={visual.surface4}>{t("ic.commander")}:</span>{" "}
          {selected.commander.split("@")[0]}
        </span>
        <span>
          <span className={visual.surface5}>{t("ic.opened")}:</span>{" "}
          {new Date(selected.opened_at).toISOString().slice(0, 16).replace("T", " ")}
        </span>
        {selected.resolved_at && (
          <span>
            <span className={visual.surface6}>{t("ic.resolved")}:</span>{" "}
            {new Date(selected.resolved_at).toISOString().slice(0, 16).replace("T", " ")}
          </span>
        )}
      </div>
    </div>
  );
}
