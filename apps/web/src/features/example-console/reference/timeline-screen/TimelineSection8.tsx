import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";
import visual from "../TimelineScreen.module.css";

interface TimelineSection8Props {
  t: (key: string, fallback?: string) => string;
  filteredEvents: E.Event[];
  setFilter: Dispatch<SetStateAction<string>>;
  filter: string;
}

export function TimelineSection8({ t, filteredEvents, setFilter, filter }: TimelineSection8Props) {
  return (
    <div className={visual.row9}>
      <Icon name="menu" size={12} className={visual.surface17} />
      <span className={visual.label5}>{t("tl.eventStream")}</span>
      <span className="chip">{filteredEvents.length}</span>
      <div className={visual.row10}>
        {(
          [
            ["all", t("tl.filterAll")],
            ["task", "task"],
            ["tool", "tool"],
            ["policy", "policy"],
            ["evidence", "evidence"],
          ] as const
        ).map(([v, l]) => (
          <button
            key={v}
            onClick={() => {
              setFilter(v);
            }}
            className="btn sm ghost"
            style={{
              color: filter === v ? "var(--accent)" : "var(--fg-muted)",
              background: filter === v ? "var(--accent-dim)" : "transparent",
            }}
          >
            {l}
          </button>
        ))}
      </div>
    </div>
  );
}
