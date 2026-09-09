import type * as E from "../exampleTypes";
import { Icon } from "./Icon";
import visual from "./MetricCard.module.css";
import { Sparkline } from "./Sparkline";

/** Reference: components/charts.jsx; EXAMPLE ONLY. */
export const MetricCard = ({
  label,
  value,
  sub,
  bar,
  barColor,
  trend,
  unknownWarn,
  spark,
  sparkColor,
}: E.MetricProps) => (
  <div className={`panel ${visual.panel ?? ""}`}>
    <div
      className={visual.row}
      style={{ color: unknownWarn ? "var(--unknown)" : "var(--fg-faint)" }}
    >
      {unknownWarn && <Icon name="q" size={10} />}
      {label}
      {trend != null && (
        <span
          className={visual.caption}
          style={{ color: trend >= 0 ? "var(--success)" : "var(--danger)" }}
        >
          {trend >= 0 ? "▲" : "▼"} {Math.abs(trend).toFixed(1)}%
        </span>
      )}
    </div>
    <div className={visual.row2}>
      <div className={visual.label}>{value}</div>
      {spark && (
        <Sparkline data={spark} width={80} height={22} stroke={sparkColor ?? "var(--accent)"} />
      )}
    </div>
    {sub && <div className={visual.label2}>{sub}</div>}
    {bar != null && (
      <div className={visual.indicator}>
        <div
          className={visual.surface}
          style={{
            width: `${String(Math.min(bar, 1) * 100)}%`,
            background: barColor ?? "var(--accent)",
          }}
        />
      </div>
    )}
  </div>
);
