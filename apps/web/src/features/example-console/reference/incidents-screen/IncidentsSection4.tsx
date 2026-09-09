import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import visual from "../IncidentsScreen.module.css";
import { IncidentsSection5 } from "./IncidentsSection5";

interface IncidentsSection4Props {
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
}

export function IncidentsSection4({
  t,
  filtered,
  selectedId,
  sevMap,
  stMap,
  setSelectedId,
}: IncidentsSection4Props) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.label}>{t("ic.queue")}</div>
      <IncidentsSection5 {...{ filtered, selectedId, sevMap, stMap, setSelectedId, t }} />
    </div>
  );
}
