import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ModelRegistryScreen.module.css";

interface ModelRegistrySection5Props {
  filtered: FixtureTypes.RegisteredModel[];
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
  cols: string;
}

export function ModelRegistrySection5({
  filtered,
  selectedId,
  setSelectedId,
  cols,
}: ModelRegistrySection5Props) {
  return (
    <div className={visual.surface}>
      {filtered.map((m) => {
        const active = m.id === selectedId;
        return (
          <div
            key={m.id}
            className={`row ${visual.surface2 ?? ""}`}
            onClick={() => {
              setSelectedId(m.id);
            }}
            style={{
              gridTemplateColumns: cols,
              background: active ? "var(--bg-hover)" : undefined,
              borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
            }}
          >
            <div className={`row-cell-wrap ${visual.surface3 ?? ""}`}>
              <div className={visual.label}>{m.family}</div>
              <div className={visual.row}>
                {m.tags.slice(0, 2).map((tag) => (
                  <span key={tag} className={`chip ${visual.caption ?? ""}`}>
                    {tag}
                  </span>
                ))}
                {m.tags.length > 2 && <span className={visual.caption2}>+{m.tags.length - 2}</span>}
              </div>
            </div>
            <span className={visual.label2}>{m.provider}</span>
            <span className={`mono ${visual.caption3 ?? ""}`}>{m.released}</span>
            <span className={`mono ${visual.caption4 ?? ""}`}>
              {(m.context / 1000).toFixed(0)}k
            </span>
            <span className={`chip ${visual.caption5 ?? ""}`}>{m.license.slice(0, 14)}</span>
          </div>
        );
      })}
    </div>
  );
}
