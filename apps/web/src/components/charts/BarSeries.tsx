import { num } from "./fmt";

export interface BarDatum {
  label: string;
  values: readonly number[];
}

function Grid({
  padL,
  w,
  h,
  padT,
  max,
}: {
  padL: number;
  w: number;
  h: number;
  padT: number;
  max: number;
}) {
  return (
    <>
      {[0, 0.25, 0.5, 0.75, 1].map((r) => (
        <g key={r}>
          <line
            x1={padL}
            x2={padL + w}
            y1={padT + h - r * h}
            y2={padT + h - r * h}
            stroke="var(--border-subtle)"
          />
          <text
            x={padL - 6}
            y={padT + h - r * h + 3}
            textAnchor="end"
            fontSize="9"
            fontFamily="var(--font-mono)"
            fill="var(--fg-faint)"
          >
            {num(Math.round(max * r))}
          </text>
        </g>
      ))}
    </>
  );
}

/** 堆叠柱状图。 */
export function BarSeries({
  data,
  series,
  width = 480,
  height = 160,
  showLabels = true,
  showGrid = true,
}: {
  data: readonly BarDatum[];
  series: readonly { key: string; color: string }[];
  width?: number;
  height?: number;
  showLabels?: boolean;
  showGrid?: boolean;
}) {
  if (data.length === 0) {
    return null;
  }
  const pad = { l: 32, r: 8, t: 8, b: showLabels ? 22 : 8 };
  const w = width - pad.l - pad.r;
  const h = height - pad.t - pad.b;
  const totals = data.map((d) => d.values.reduce((a, b) => a + b, 0));
  const max = Math.max(...totals) || 1;
  const barW = (w / data.length) * 0.7;
  const gap = (w / data.length) * 0.3;
  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${num(width)} ${num(height)}`}
      aria-hidden="true"
    >
      {showGrid && <Grid padL={pad.l} w={w} h={h} padT={pad.t} max={max} />}
      {data.map((d, i) => (
        <BarGroup
          key={d.label}
          datum={d}
          series={series}
          x={pad.l + i * (barW + gap) + gap / 2}
          barW={barW}
          padT={pad.t}
          h={h}
          max={max}
          showLabels={showLabels}
          height={height}
        />
      ))}
    </svg>
  );
}

function BarGroup({
  datum,
  series,
  x,
  barW,
  padT,
  h,
  max,
  showLabels,
  height,
}: {
  datum: BarDatum;
  series: readonly { key: string; color: string }[];
  x: number;
  barW: number;
  padT: number;
  h: number;
  max: number;
  showLabels: boolean;
  height: number;
}) {
  let stackY = 0;
  return (
    <g transform={`translate(${num(x)},0)`}>
      {series.map((s, j) => {
        const v = datum.values[j] ?? 0;
        const bh = (v / max) * h;
        const y = padT + h - stackY - bh;
        stackY += bh;
        return <rect key={s.key} x={0} y={y} width={barW} height={bh} fill={s.color} rx="1" />;
      })}
      {showLabels && (
        <text
          x={barW / 2}
          y={height - 6}
          textAnchor="middle"
          fontSize="9"
          fontFamily="var(--font-mono)"
          fill="var(--fg-faint)"
        >
          {datum.label}
        </text>
      )}
    </g>
  );
}
