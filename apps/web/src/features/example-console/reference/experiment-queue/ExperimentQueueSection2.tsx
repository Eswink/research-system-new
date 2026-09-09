import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ExperimentQueue.module.css";
import { ExperimentQueueSection3 } from "./ExperimentQueueSection3";

interface ExperimentQueueSection2Props {
  queue: FixtureTypes.Experiment[];
  selectedId: string;
  onSelect: (id: string) => void;
}

export function ExperimentQueueSection2({
  queue,
  selectedId,
  onSelect,
}: ExperimentQueueSection2Props) {
  return (
    <div className={visual.surface2}>
      {queue.map((e) => {
        const selected = e.id === selectedId;
        return (
          <div
            key={e.id}
            onClick={() => {
              onSelect(e.id);
            }}
            className={visual.surface3}
            style={{
              background: selected ? "var(--bg-hover)" : "transparent",
              borderLeft: `2px solid ${selected ? "var(--accent)" : "transparent"}`,
            }}
          >
            <ExperimentQueueSection3 {...{ e }} />
            <div className={visual.row3}>
              {Object.entries(e.variables)
                .slice(0, 4)
                .map(([k, v]) => (
                  <span key={k} className={`chip ${visual.caption3 ?? ""}`}>
                    <span className={visual.surface4}>{k}:</span>{" "}
                    {Array.isArray(v) ? `[${String(v.length)}]` : v}
                  </span>
                ))}
            </div>
            {(e.status === "RUNNING" || e.progress > 0) && (
              <div className={visual.indicator}>
                <div
                  className={visual.surface5}
                  style={{
                    width: `${String(e.progress * 100)}%`,
                    background: e.status === "FAILED" ? "var(--danger)" : "var(--accent)",
                  }}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
