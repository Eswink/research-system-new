import type { CSSProperties, ReactNode } from "react";

import { num } from "./fmt";

function DonutArc({
  cx,
  cy,
  r,
  thickness,
  color,
  dash,
  gap,
  rot,
}: {
  cx: number;
  cy: number;
  r: number;
  thickness: number;
  color: string;
  dash: number;
  gap: number;
  rot: number;
}) {
  return (
    <circle
      cx={cx}
      cy={cy}
      r={r}
      fill="none"
      stroke={color}
      strokeWidth={thickness}
      strokeDasharray={`${num(dash)} ${num(gap)}`}
      transform={`rotate(${num(rot)} ${num(cx)} ${num(cy)})`}
    />
  );
}

/** 环形占比图。 */
export function Donut({
  values,
  size = 88,
  thickness = 12,
  center,
}: {
  values: readonly { label: string; value: number; color: string }[];
  size?: number;
  thickness?: number;
  center?: ReactNode;
}) {
  const cx = size / 2;
  const cy = size / 2;
  const r = (size - thickness) / 2;
  const total = values.reduce((a, v) => a + v.value, 0) || 1;
  const C = 2 * Math.PI * r;
  let acc = 0;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${num(size)} ${num(size)}`} aria-hidden="true">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--bg-sunken)" strokeWidth={thickness} />
      {values.map((v) => {
        const arc = (
          <DonutArc
            key={v.label}
            cx={cx}
            cy={cy}
            r={r}
            thickness={thickness}
            color={v.color}
            dash={(v.value / total) * C}
            gap={C - (v.value / total) * C}
            rot={(acc / total) * 360 - 90}
          />
        );
        acc += v.value;
        return arc;
      })}
      {center !== undefined && (
        <foreignObject x="0" y="0" width={size} height={size}>
          <div style={centerStyle}>{center}</div>
        </foreignObject>
      )}
    </svg>
  );
}

const centerStyle: CSSProperties = {
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  pointerEvents: "none",
};
