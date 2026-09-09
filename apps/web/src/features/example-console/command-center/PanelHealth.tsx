import { HealthGauge } from "../reference/HealthGauge";
import { Panel } from "./Panel";
import visual from "./PanelHealth.module.css";

/** Reference: Command Center.html; every metric is a fixed example. */
export const PanelHealth = () => (
  <Panel kicker="MISSION" title="Overall Health" className={visual.surface}>
    <div className={visual.column}>
      <HealthGauge value={82} size={140} label="MISSION SCORE" />
      <div className={visual.grid}>
        {(
          [
            ["INFRASTRUCTURE", 94, "var(--success)"],
            ["MODELS", 88, "var(--success)"],
            ["BUDGET", 62, "var(--warn)"],
            ["EVIDENCE", 78, "var(--warn)"],
          ] as const
        ).map(([k, v, c]) => (
          <div key={k} className={visual.surface2}>
            <div className={visual.caption}>{k}</div>
            <div className={visual.row}>
              <div className={visual.indicator}>
                <div
                  className={visual.surface3}
                  style={{ width: `${String(v)}%`, background: c }}
                />
              </div>
              <span className={visual.label} style={{ color: c }}>
                {v}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  </Panel>
);
