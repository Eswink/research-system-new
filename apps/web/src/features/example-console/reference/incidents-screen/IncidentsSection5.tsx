import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import visual from "../IncidentsScreen.module.css";
import { IncidentsSection7 } from "./IncidentsSection7";

interface IncidentsSection5Props {
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
  t: (key: string, fallback?: string) => string;
}

export function IncidentsSection5({
  filtered,
  selectedId,
  sevMap,
  stMap,
  setSelectedId,
  t,
}: IncidentsSection5Props) {
  return (
    <div className={visual.surface}>
      {filtered.map((inc) => {
        const active = inc.id === selectedId;
        const sev = sevMap[inc.severity] ?? { color: "var(--unknown)", label: inc.severity };
        const st = stMap[inc.status] ?? { tone: "unknown", label: inc.status };
        return (
          <div
            key={inc.id}
            onClick={() => {
              setSelectedId(inc.id);
            }}
            className={visual.surface2}
            style={{
              background: active ? "var(--bg-hover)" : "transparent",
              borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
            }}
          >
            <IncidentsSection7 {...{ sev, st, inc }} />
            <div className={visual.label2}>{inc.title}</div>
            <div className={visual.row2}>
              <span>{new Date(inc.opened_at).toISOString().slice(5, 16).replace("T", " ")}</span>
              <span>·</span>
              <span>
                {inc.duration_min != null ? `${String(inc.duration_min)}m` : t("ic.ongoing")}
              </span>
              <span>·</span>
              <span>{inc.commander.split("@")[0]}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
