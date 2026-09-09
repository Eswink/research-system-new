import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ExperimentQueue.module.css";
import { ExpStatusBadge } from "../ExpStatusBadge";
import { PriorityChip } from "../PriorityChip";

interface ExperimentQueueSection3Props {
  e: FixtureTypes.Experiment;
}

export function ExperimentQueueSection3({ e }: ExperimentQueueSection3Props) {
  return (
    <div className={visual.row2}>
      <ExpStatusBadge status={e.status} />
      <span className={visual.label2}>{e.label}</span>
      <PriorityChip priority={e.priority} />
      <span className={visual.caption2}>
        {e.status === "RUNNING"
          ? `ETA ${String(e.eta_min)}m`
          : e.status === "QUEUED"
            ? `~${String(e.eta_min)}m`
            : e.status === "PAUSED"
              ? "paused"
              : e.duration_s
                ? `${String(Math.round(e.duration_s / 60))}m`
                : "—"}
      </span>
    </div>
  );
}
