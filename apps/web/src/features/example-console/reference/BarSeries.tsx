interface BarSeriesProps {
  data: { label: string; values: number[] }[];
  series: { color: string; label?: string; key?: string }[];
  width?: number;
  height?: number;
  showLabels?: boolean;
  showGrid?: boolean;
}

interface BarGeometry {
  pad: { l: number; r: number; t: number; b: number };
  w: number;
  h: number;
  max: number;
  barW: number;
  gap: number;
}

/** Reference: components/charts.jsx; EXAMPLE ONLY. */
export const BarSeries = ({
  data,
  series,
  width = 480,
  height = 160,
  showLabels = true,
  showGrid = true,
}: BarSeriesProps) => {
  if (!data.length) return null;
  const geometry = buildBarGeometry({ data, width, height, showLabels });
  return (
    <svg width={width} height={height} viewBox={`0 0 ${String(width)} ${String(height)}`}>
      {showGrid && <BarGrid geometry={geometry} />}
      <BarGroups {...{ data, series, height, showLabels, geometry }} />
    </svg>
  );
};

function buildBarGeometry({
  data,
  width,
  height,
  showLabels,
}: {
  data: BarSeriesProps["data"];
  width: number;
  height: number;
  showLabels: boolean;
}): BarGeometry {
  const pad = { l: 32, r: 8, t: 8, b: showLabels ? 22 : 8 };
  const w = width - pad.l - pad.r;
  const h = height - pad.t - pad.b;
  const totals = data.map((item) => item.values.reduce((sum, value) => sum + value, 0));
  const max = Math.max(...totals) || 1;
  return {
    pad,
    w,
    h,
    max,
    barW: (w / data.length) * 0.7,
    gap: (w / data.length) * 0.3,
  };
}

function BarGrid({ geometry }: { geometry: BarGeometry }) {
  const { pad, w, h, max } = geometry;
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
            strokeWidth="1"
          />
          <text
            x={pad.l - 6}
            y={pad.t + h - ratio * h + 3}
            textAnchor="end"
            fontSize="9"
            fontFamily="var(--font-mono)"
            fill="var(--fg-faint)"
          >
            {Math.round(max * ratio)}
          </text>
        </g>
      ))}
    </>
  );
}

function BarGroups({
  data,
  series,
  height,
  showLabels,
  geometry,
}: Required<Pick<BarSeriesProps, "data" | "series" | "height" | "showLabels">> & {
  geometry: BarGeometry;
}) {
  return (
    <>
      {data.map((item, index) => (
        <BarGroup key={index} {...{ item, index, series, height, showLabels, geometry }} />
      ))}
    </>
  );
}

function BarGroup({
  item,
  index,
  series,
  height,
  showLabels,
  geometry,
}: {
  item: BarSeriesProps["data"][number];
  index: number;
  series: BarSeriesProps["series"];
  height: number;
  showLabels: boolean;
  geometry: BarGeometry;
}) {
  const { pad, h, max, barW, gap } = geometry;
  let stackY = 0;
  return (
    <g transform={`translate(${String(pad.l + index * (barW + gap) + gap / 2)},0)`}>
      {series.map((entry, seriesIndex) => {
        const value = item.values[seriesIndex] ?? 0;
        const barHeight = (value / max) * h;
        const y = pad.t + h - stackY - barHeight;
        stackY += barHeight;
        return (
          <rect
            key={seriesIndex}
            x={0}
            y={y}
            width={barW}
            height={barHeight}
            fill={entry.color}
            rx="1"
          />
        );
      })}
      {showLabels && <BarLabel label={item.label} x={barW / 2} y={height - 6} />}
    </g>
  );
}

function BarLabel({ label, x, y }: { label: string; x: number; y: number }) {
  return (
    <text
      x={x}
      y={y}
      textAnchor="middle"
      fontSize="9"
      fontFamily="var(--font-mono)"
      fill="var(--fg-faint)"
    >
      {label}
    </text>
  );
}
