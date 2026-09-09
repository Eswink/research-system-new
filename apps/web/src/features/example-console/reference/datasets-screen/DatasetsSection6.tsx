import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../DatasetsScreen.module.css";
import { DatasetsLabel } from "./DatasetsLabel";

interface DatasetsSection6Props {
  filtered: FixtureTypes.Dataset[];
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
  t: (key: string, fallback?: string) => string;
}

export function DatasetsSection6({
  filtered,
  selectedId,
  setSelectedId,
  t,
}: DatasetsSection6Props) {
  return (
    <div className={visual.surface2}>
      {filtered.map((d) => {
        const active = d.id === selectedId;
        return (
          <div
            key={d.id}
            className={`row ${visual.surface3 ?? ""}`}
            onClick={() => {
              setSelectedId(d.id);
            }}
            style={{
              background: active ? "var(--bg-hover)" : undefined,
              borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
            }}
          >
            <div className={`row-cell-wrap ${visual.surface4 ?? ""}`}>
              <div className={visual.label}>{d.name}</div>
              <div className={visual.row}>
                {d.tags.slice(0, 2).map((tg) => (
                  <span key={tg} className={`chip ${visual.caption ?? ""}`}>
                    {tg}
                  </span>
                ))}
                {d.tags.length > 2 && <span className={visual.caption2}>+{d.tags.length - 2}</span>}
              </div>
            </div>
            <span className={`mono ${visual.label2 ?? ""}`}>{d.version}</span>
            <span className={visual.label3}>
              {d.rows == null ? <span className="empty-mark">—</span> : d.rows.toLocaleString()}
            </span>
            <span className={visual.label4}>
              {d.size_mb < 1000 ? `${String(d.size_mb)} MB` : `${(d.size_mb / 1024).toFixed(1)} GB`}
            </span>
            <span className={`chip ${visual.caption3 ?? ""}`}>{d.format}</span>
            <DatasetsLabel {...{ d, t }} />
          </div>
        );
      })}
    </div>
  );
}
