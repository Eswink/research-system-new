import type * as E from "../exampleTypes";
import visual from "./BudgetMetricCard.module.css";

/** Reference: screens/Budget.jsx; EXAMPLE ONLY. */
export const MetricCard = ({ label, value, sub, bar, barColor, unknownWarn }: E.MetricProps) => (
  <div
    className={`panel ${visual.panel ?? ""}`}
    style={{
      border: unknownWarn ? "1px dashed var(--unknown-line)" : "1px solid var(--border)",
      background: unknownWarn ? "var(--unknown-dim)" : "var(--bg-panel)",
    }}
  >
    <div className={visual.caption}>{label}</div>
    <div className={visual.label}>{value}</div>
    <div className={visual.label2} style={{ marginBottom: bar != null ? 8 : 0 }}>
      {sub}
    </div>
    {bar != null && (
      <div className={visual.indicator}>
        <div
          className={visual.surface}
          style={{ width: `${String(Math.min(100, bar * 100))}%`, background: barColor }}
        />
      </div>
    )}
  </div>
);
