import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";
import visual from "../IncidentsScreen.module.css";
import { IncidentsImpact } from "./IncidentsImpact";
import { IncidentsSection } from "./IncidentsSection";
import { IncidentsSection4 } from "./IncidentsSection4";

interface IncidentsSection2Props {
  t: (key: string, fallback?: string) => string;
  filtered: (
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
      }
  )[];
  selectedId: string;
  sevMap: Record<string, { color: string; label: string; icon?: string }>;
  stMap: Record<string, E.BadgeProps>;
  setSelectedId: Dispatch<SetStateAction<string>>;
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
      }
    | undefined;
}

export function IncidentsSection2({
  t,
  filtered,
  selectedId,
  sevMap,
  stMap,
  setSelectedId,
  selected,
}: IncidentsSection2Props) {
  return (
    <div className={visual.grid2}>
      {/* List */}
      <IncidentsSection4 {...{ t, filtered, selectedId, sevMap, stMap, setSelectedId }} />

      {/* Detail */}
      {selected && (
        <div className={`panel ${visual.panel2 ?? ""}`}>
          <IncidentsSection {...{ stMap, selected, sevMap, t }} />

          <IncidentsImpact {...{ t, selected }} />

          <div className={visual.row7}>
            <button className={`btn sm ghost ${visual.action ?? ""}`}>
              <Icon name="external" size={11} /> {t("ic.export")}
            </button>
            {selected.status !== "resolved" && (
              <button className="btn primary sm">
                <Icon name="check" size={11} /> {t("ic.markResolved")}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
