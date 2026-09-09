import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../CompareScreen.module.css";
import { RunStateBadge } from "../RunStateBadge";

interface CompareSection9Props {
  allRuns: FixtureTypes.Run[];
  selected: string[];
  toggleRun: (id: string) => void;
}

export function CompareSection9({ allRuns, selected, toggleRun }: CompareSection9Props) {
  return (
    <div className={visual.column2}>
      {allRuns.map((r) => {
        const on = selected.includes(r.id);
        const idx = selected.indexOf(r.id);
        return (
          <label
            key={r.id}
            className={visual.row8}
            style={{
              background: on ? "var(--accent-dim)" : "var(--bg-raised)",
              border: `1px solid ${on ? "var(--accent-line)" : "var(--border)"}`,
            }}
          >
            <input
              type="checkbox"
              checked={on}
              onChange={() => {
                toggleRun(r.id);
              }}
            />
            {on && (
              <span className={`mono ${visual.caption6 ?? ""}`}>
                {String.fromCharCode(65 + idx)}
              </span>
            )}
            <div className={visual.surface11}>
              <div className={visual.label10}>{r.label}</div>
              <div className={`mono ${visual.caption7 ?? ""}`}>
                {r.id.slice(0, 20)} · {new Date(r.started_at).toISOString().slice(0, 10)}
              </div>
            </div>
            <RunStateBadge state={r.state} />
          </label>
        );
      })}
    </div>
  );
}
