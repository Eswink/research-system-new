import FIX_PHASES from "../../data/phases.json";
import visual from "../TimelineScreen.module.css";
import { TimelineSection4 } from "./TimelineSection4";
import { TimelineSection7 } from "./TimelineSection7";

interface TimelineSectionProps {
  totalDuration: number;
}

export function TimelineSection({ totalDuration }: TimelineSectionProps) {
  return (
    <div className={visual.surface10}>
      {/* Time ruler */}
      <TimelineSection7 {...{ totalDuration }} />

      {FIX_PHASES.map((phase) => (
        <div key={phase.id} className={visual.surface13}>
          <div className={visual.label3}>
            {phase.name}{" "}
            <span className={visual.surface14}>
              +{phase.start}m → +{phase.end}m
            </span>
          </div>
          {phase.tasks.map((task) => {
            const statusColor = {
              SUCCEEDED: "var(--success)",
              RUNNING: "var(--accent)",
              FAILED: "var(--danger)",
              PENDING: "var(--fg-faint)",
            }[task.status];
            return (
              <div key={task.id} className={visual.grid2}>
                <div className={visual.row8}>
                  <div className={visual.surface15} style={{ background: statusColor }} />
                  <span className={visual.label4}>{task.name}</span>
                  {task.attempt > 1 && (
                    <span title={`attempt ${String(task.attempt)}`} className={visual.caption2}>
                      ×{task.attempt}
                    </span>
                  )}
                </div>
                <TimelineSection4 {...{ task, totalDuration, statusColor }} />
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
