import type * as R from "react";
import type * as E from "../exampleTypes";

interface LineSeriesProps {
  data: E.LineData[];
  xLabels?: string[];
  width?: number;
  height?: number;
  colors?: string[];
  yFormat?: (value: number) => R.ReactNode;
  showGrid?: boolean;
}

interface LineGeometry {
  pad: { l: number; r: number; t: number; b: number };
  w: number;
  h: number;
  min: number;
  range: number;
  step: number;
  palette: string[];
}

/** Reference: components/charts.jsx; EXAMPLE ONLY. */
export const LineSeries = ({
  data,
  xLabels,
  width = 640,
  height = 220,
  colors,
  yFormat = (v) => v,
  showGrid = true,
}: LineSeriesProps) => {
  const geometry = buildLineGeometry({ data, width, height, colors });
  return (
    <svg width={width} height={height} viewBox={`0 0 ${String(width)} ${String(height)}`}>
      {showGrid && <LineGrid geometry={geometry} yFormat={yFormat} />}
      <LinePaths data={data} geometry={geometry} />
      {xLabels !== undefined && (
        <LineXLabels labels={xLabels} height={height} geometry={geometry} />
      )}
    </svg>
  );
};

function buildLineGeometry({
  data,
  width,
  height,
  colors,
}: {
  data: E.LineData[];
  width: number;
  height: number;
  colors: string[] | undefined;
}): LineGeometry {
  const pad = { l: 40, r: 12, t: 10, b: 24 };
  const w = width - pad.l - pad.r;
  const h = height - pad.t - pad.b;
  const all = data.flatMap((entry) => entry.values);
  const max = Math.max(...all) || 1;
  const min = Math.min(0, ...all);
  return {
    pad,
    w,
    h,
    min,
    range: max - min || 1,
    step: w / ((data[0]?.values.length ?? 1) - 1),
    palette: colors ?? [
      "var(--accent)",
      "var(--success)",
      "var(--warn)",
      "var(--unknown)",
      "var(--danger)",
      "var(--fg-muted)",
    ],
  };
}

function LineGrid({
  geometry,
  yFormat,
}: {
  geometry: LineGeometry;
  yFormat: (value: number) => R.ReactNode;
}) {
  const { pad, w, h, min, range } = geometry;
  return (
    <>
      {[0, 0.25, 0.5, 0.75, 1].map((ratio, index) => (
        <g key={index}>
          <line
            x1={pad.l}
            x2={pad.l + w}
            y1={pad.t + h - ratio * h}
            y2={pad.t + h - ratio * h}
            stroke="var(--border-subtle)"
          />
          <text
            x={pad.l - 6}
            y={pad.t + h - ratio * h + 3}
            textAnchor="end"
            fontSize="9"
            fontFamily="var(--font-mono)"
            fill="var(--fg-faint)"
          >
            {yFormat(Math.round(min + range * ratio))}
          </text>
        </g>
      ))}
    </>
  );
}

function LinePaths({ data, geometry }: { data: E.LineData[]; geometry: LineGeometry }) {
  const { pad, h, min, range, step, palette } = geometry;
  return (
    <>
      {data.map((entry, dataIndex) => {
        const points = entry.values.map((value, index) => [
          pad.l + index * step,
          pad.t + h - ((value - min) / range) * h,
        ]);
        const color = palette[dataIndex % palette.length];
        return <LinePath key={dataIndex} points={points} color={color} />;
      })}
    </>
  );
}

function LinePath({ points, color }: { points: number[][]; color: string | undefined }) {
  const path = "M " + points.map((point) => point.join(" ")).join(" L ");
  return (
    <g>
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {points.map((point, index) => (
        <circle key={index} cx={point[0]} cy={point[1]} r="1.6" fill={color} />
      ))}
    </g>
  );
}

function LineXLabels({
  labels,
  height,
  geometry,
}: {
  labels: string[];
  height: number;
  geometry: LineGeometry;
}) {
  return (
    <>
      {labels.map((label, index) => (
        <text
          key={index}
          x={geometry.pad.l + index * geometry.step}
          y={height - 6}
          textAnchor="middle"
          fontSize="9"
          fontFamily="var(--font-mono)"
          fill="var(--fg-faint)"
        >
          {label}
        </text>
      ))}
    </>
  );
}
