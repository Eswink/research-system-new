import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../CompareScreen.module.css";
import { Icon } from "../Icon";
import { RunStateBadge } from "../RunStateBadge";

interface CompareSection4Props {
  selectedRuns: FixtureTypes.Run[];
  toggleRun: (id: string) => void;
}

export function CompareSection4({ selectedRuns, toggleRun }: CompareSection4Props) {
  return (
    <div className={visual.row2}>
      {selectedRuns.map((r, i) => (
        <div
          key={r.id}
          className={visual.row3}
          style={{
            borderLeft: `2px solid ${String(
              ["var(--accent)", "var(--warn)", "var(--success)", "var(--unknown)"][i],
            )}`,
          }}
        >
          <span className={`mono ${visual.caption ?? ""}`}>{String.fromCharCode(65 + i)}</span>
          <span className={visual.surface}>{r.label}</span>
          <RunStateBadge state={r.state} />
          <button
            className={`btn sm ghost ${visual.action ?? ""}`}
            onClick={() => {
              toggleRun(r.id);
            }}
          >
            <Icon name="x" size={9} />
          </button>
        </div>
      ))}
    </div>
  );
}
