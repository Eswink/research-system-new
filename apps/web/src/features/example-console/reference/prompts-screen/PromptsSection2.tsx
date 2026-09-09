import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import { Icon } from "../Icon";
import visual from "../PromptsScreen.module.css";
import { PromptStatusBadge } from "../PromptStatusBadge";

interface PromptsSection2Props {
  t: (key: string, fallback?: string) => string;
  filtered: FixtureTypes.Prompt[];
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
}

export function PromptsSection2({ t, filtered, selectedId, setSelectedId }: PromptsSection2Props) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="book" size={12} className={visual.surface} />
        <span className={visual.label}>{t("pr.listHead")}</span>
        <span className="chip">{filtered.length}</span>
      </div>
      <div className={visual.surface2}>
        {filtered.map((p) => {
          const active = p.id === selectedId;
          return (
            <div
              key={p.id}
              onClick={() => {
                setSelectedId(p.id);
              }}
              className={visual.surface3}
              style={{
                background: active ? "var(--bg-hover)" : "transparent",
                borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
              }}
            >
              <div className={visual.row2}>
                <PromptStatusBadge status={p.status} />
                <span className={`mono ${visual.caption ?? ""}`}>{p.latest_version}</span>
              </div>
              <div className={visual.label2}>{p.name}</div>
              <div className={visual.row3}>
                <span>{p.versions}v</span>
                <span>{p.usage_7d.toLocaleString()}/7d</span>
                {p.avg_latency_ms && <span>{p.avg_latency_ms}ms</span>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
