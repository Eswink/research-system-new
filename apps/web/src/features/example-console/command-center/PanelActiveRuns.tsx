import FIX_RUNS_HISTORY from "../data/runs-history.json";
import { DigestText } from "../reference/DigestText";
import { Panel } from "./Panel";
import visual from "./PanelActiveRuns.module.css";

/** Reference: Command Center.html; every metric is a fixed example. */
export const PanelActiveRuns = () => (
  <Panel
    kicker="OPERATIONS"
    title="Active Runs"
    right={
      <>
        <span className={`chip ${visual.surface2 ?? ""}`}>
          {FIX_RUNS_HISTORY.filter((r) => r.live).length} LIVE
        </span>
      </>
    }
    className={visual.surface}
  >
    <div className={visual.column}>
      {FIX_RUNS_HISTORY.filter((r) => r.live === true || r.state === "RUNNING")
        .slice(0, 3)
        .map((r) => (
          <div key={r.id} className={visual.column2}>
            <div className={visual.row}>
              <div className={`pulse-dot ${visual.indicator ?? ""}`} />
              <span className={visual.label}>{r.label}</span>
              <DigestText value={r.id} length={12} prefix={false} />
              <span className={visual.caption}>elapsed {Math.round(r.duration_s / 60)}m</span>
            </div>
            <div className={visual.row2}>
              <div className={visual.indicator2}>
                <div
                  className={visual.indicator3}
                  style={{ width: `${String((r.tasks_done / r.tasks_total) * 100)}%` }}
                />
              </div>
              <span className={visual.label2}>
                {r.tasks_done}/{r.tasks_total}
              </span>
              <span
                className={visual.label3}
                style={{ color: r.tasks_failed > 0 ? "var(--danger)" : "var(--fg-faint)" }}
              >
                {r.tasks_failed > 0 ? `${String(r.tasks_failed)} fail` : "ok"}
              </span>
              <span className={visual.label4}>${(r.spent_minor / 100000).toFixed(2)}</span>
            </div>
          </div>
        ))}
    </div>
  </Panel>
);
