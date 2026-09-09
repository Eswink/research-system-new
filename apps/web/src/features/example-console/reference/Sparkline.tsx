import visual from "./Sparkline.module.css";

/** Reference: components/charts.jsx; EXAMPLE ONLY. */
export const Sparkline = ({
  data,
  width = 96,
  height = 22,
  stroke = "var(--accent)",
  fill = "var(--accent-dim)",
  strokeWidth = 1.4,
}: {
  data: number[];
  width?: number;
  height?: number;
  stroke?: string;
  fill?: string;
  strokeWidth?: number;
}) => {
  if (data.length < 2) return null;
  const min = Math.min(...data),
    max = Math.max(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1);
  const points = data.map((v, i) => [i * step, height - ((v - min) / range) * (height - 4) - 2]);
  const linePath = "M " + points.map((p) => p.join(" ")).join(" L ");
  const areaPath = linePath + ` L ${String(width)} ${String(height)} L 0 ${String(height)} Z`;
  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${String(width)} ${String(height)}`}
      className={visual.chart}
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
      {points.at(-1) && (
        <circle cx={points.at(-1)?.[0]} cy={points.at(-1)?.[1]} r={2} fill={stroke} />
      )}
    </svg>
  );
};
