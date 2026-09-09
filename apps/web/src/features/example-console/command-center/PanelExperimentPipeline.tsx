import FIX_EXPERIMENT_QUEUE from "../data/experiment-queue.json";
import { Panel } from "./Panel";
import visual from "./PanelExperimentPipeline.module.css";

/** Reference: Command Center.html; every metric is a fixed example. */
export const PanelExperimentPipeline = () => (
  <Panel
    kicker="EXPERIMENTS"
    title="Queue Pipeline"
    right={
      <>
        <span className={visual.caption}>
          {FIX_EXPERIMENT_QUEUE.filter((e) => e.status === "RUNNING").length} running ·{" "}
          {FIX_EXPERIMENT_QUEUE.filter((e) => e.status === "QUEUED").length} queued
        </span>
      </>
    }
    className={visual.surface}
  >
    <PanelExperimentPipelineSection {...{}} />
  </Panel>
);

function PanelExperimentPipelineSection() {
  return (
    <div className={visual.column}>
      {FIX_EXPERIMENT_QUEUE.slice(0, 5).map((e) => (
        <div key={e.id} className={visual.grid}>
          <span
            className={visual.caption2}
            style={{
              color:
                e.status === "RUNNING"
                  ? "var(--accent)"
                  : e.status === "FAILED"
                    ? "var(--danger)"
                    : e.status === "SUCCEEDED"
                      ? "var(--success)"
                      : "var(--fg-faint)",
            }}
          >
            {e.status}
          </span>
          <span className={visual.label}>{e.label}</span>
          <div className={visual.indicator}>
            <div
              className={visual.surface2}
              style={{
                width: `${String(e.progress * 100)}%`,
                background: e.status === "FAILED" ? "var(--danger)" : "var(--accent)",
              }}
            />
          </div>
          <span className={visual.caption3}>
            {e.status === "SUCCEEDED"
              ? `${String(
                  e.duration_s === undefined ? "UNKNOWN" : Math.round(e.duration_s / 60),
                )}m done`
              : e.eta_min
                ? `~${String(e.eta_min)}m ETA`
                : "queued"}
          </span>
        </div>
      ))}
    </div>
  );
}
