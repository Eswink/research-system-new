import { num } from "./fmt";

/** 迷你折线（内联）。 */
export function Sparkline({
  data,
  width = 96,
  height = 22,
  stroke = "var(--accent)",
  fill = "var(--accent-dim)",
  strokeWidth = 1.4,
}: {
  data: readonly number[];
  width?: number;
  height?: number;
  stroke?: string;
  fill?: string;
  strokeWidth?: number;
}) {
  if (data.length < 2) {
    return null;
  }
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1);
  const points = data.map((v, i) => [i * step, height - ((v - min) / range) * (height - 4) - 2]);
  const linePath = "M " + points.map((p) => p.join(" ")).join(" L ");
  const areaPath = `${linePath} L ${num(width)} ${num(height)} L 0 ${num(height)} Z`;
  const last = points[points.length - 1];
  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${num(width)} ${num(height)}`}
      style={{ display: "inline-block", verticalAlign: "middle" }}
      aria-hidden="true"
    >
      <path d={areaPath} fill={fill} stroke="none" />
      <path
        d={linePath}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {last !== undefined && <circle cx={last[0]} cy={last[1]} r={2} fill={stroke} />}
    </svg>
  );
}
