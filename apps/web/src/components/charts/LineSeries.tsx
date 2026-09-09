import { num } from "./fmt";

const PALETTE = [
  "var(--accent)",
  "var(--success)",
  "var(--warn)",
  "var(--unknown)",
  "var(--danger)",
  "var(--fg-muted)",
];

interface Geo {
  padL: number;
  padT: number;
  step: number;
  h: number;
  min: number;
  range: number;
}

function LineGrid({
  padL,
  padT,
  h,
  min,
  range,
  yFormat,
  w,
}: Geo & {
  w: number;
  yFormat: (v: number) => string;
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
            fontSize={9}
            fontFamily="var(--font-mono)"
            fill="var(--fg-faint)"
          >
            {yFormat(Math.round(min + range * r))}
          </text>
        </g>
      ))}
    </>
  );
}

function LinePath({ values, color, geo }: { values: readonly number[]; color: string; geo: Geo }) {
  const { padL, padT, step, h, min, range } = geo;
  const pts = values.map((v, i) => [padL + i * step, padT + h - ((v - min) / range) * h]);
  const dPath = "M " + pts.map((p) => p.join(" ")).join(" L ");
  return (
    <g>
      <path
        d={dPath}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {pts.map((p, i) => (
        <circle key={i} cx={p[0]} cy={p[1]} r="1.6" fill={color} />
      ))}
    </g>
  );
}

/** 多序列折线。 */
export function LineSeries({
  data,
  xLabels,
  width = 640,
  height = 220,
  colors,
  yFormat = (v: number) => String(v),
  showGrid = true,
}: {
  data: readonly { label: string; values: readonly number[] }[];
  xLabels?: readonly string[];
  width?: number;
  height?: number;
  colors?: readonly string[];
  yFormat?: (v: number) => string;
  showGrid?: boolean;
}) {
  const geo = computeGeo(data, width, height);
  const palette = colors ?? PALETTE;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${num(width)} ${num(height)}`} aria-hidden>
      {showGrid && <LineGrid {...geo} w={width - geo.padL - 12} yFormat={yFormat} />}
      {data.map((d, di) => (
        <LinePath
          key={d.label}
          values={d.values}
          color={palette[di % palette.length] ?? "var(--accent)"}
          geo={geo}
        />
      ))}
      {xLabels?.map((l, i) => (
        <text
          key={`${l}-${num(i)}`}
          x={geo.padL + i * geo.step}
          y={height - 6}
          textAnchor="middle"
          fontSize={9}
          fontFamily="var(--font-mono)"
          fill="var(--fg-faint)"
        >
          {l}
        </text>
      ))}
    </svg>
  );
}
function computeGeo(
  data: readonly { values: readonly number[] }[],
  width: number,
  height: number,
): Geo & { padR: number } {
  const pad = { l: 40, r: 12, t: 10, b: 24 };
  const w = width - pad.l - pad.r;
  const h = height - pad.t - pad.b;
  const all = data.flatMap((d) => d.values);
  const max = Math.max(...all, 0) || 1;
  const min = Math.min(0, ...all);
  const range = max - min || 1;
  const step = w / Math.max((data[0]?.values.length ?? 1) - 1, 1);
  return { padL: pad.l, padT: pad.t, step, h, min, range, padR: pad.r };
}
