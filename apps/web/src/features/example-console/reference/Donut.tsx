import type * as R from "react";
import visual from "./Donut.module.css";

/** Reference: components/charts.jsx; EXAMPLE ONLY. */
export const Donut = ({
  values,
  size = 88,
  thickness = 12,
  center,
}: {
  values: { label?: string; value: number; color: string }[];
  size?: number;
  thickness?: number;
  center?: R.ReactNode;
}) => {
  const cx = size / 2,
    cy = size / 2;
  const r = (size - thickness) / 2;
  const total = values.reduce((a, v) => a + v.value, 0) || 1;
  let acc = 0;
  const C = 2 * Math.PI * r;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${String(size)} ${String(size)}`}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--bg-sunken)" strokeWidth={thickness} />
      {values.map((v, i) => {
        const frac = v.value / total;
        const dash = frac * C;
        const gap = C - dash;
        const rot = (acc / total) * 360 - 90;
        acc += v.value;
        return (
          <circle
            key={i}
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke={v.color}
            strokeWidth={thickness}
            strokeDasharray={`${String(dash)} ${String(gap)}`}
            transform={`rotate(${String(rot)} ${String(cx)} ${String(cy)})`}
            strokeLinecap="butt"
          />
        );
      })}
      {center && (
        <foreignObject x="0" y="0" width={size} height={size}>
          <div className={visual.column}>{center}</div>
        </foreignObject>
      )}
    </svg>
  );
};
