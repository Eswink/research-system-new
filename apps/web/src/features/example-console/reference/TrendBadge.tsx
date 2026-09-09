import visual from "./TrendBadge.module.css";

/** Reference: components/patterns.jsx; EXAMPLE ONLY. */
export const TrendBadge = ({
  delta,
  inverted = false,
  format = (v) => `${v > 0 ? "+" : ""}${v.toFixed(1)}%`,
}: {
  delta: number;
  inverted?: boolean;
  format?: (value: number) => string;
}) => {
  const good = inverted ? delta < 0 : delta > 0;
  const color = delta === 0 ? "var(--fg-muted)" : good ? "var(--success)" : "var(--danger)";
  return (
    <span className={visual.row} style={{ color }}>
      {delta > 0 ? "▲" : delta < 0 ? "▼" : "→"} {format(Math.abs(delta))}
    </span>
  );
};
