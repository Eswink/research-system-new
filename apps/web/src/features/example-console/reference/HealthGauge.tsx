import { gaugeArc, gaugeColor, gaugeGeometry, type GaugeGeometry } from "./gaugeGeometry";

/** Reference gauge: null/nonfinite readings have no progress arc, never a fabricated score. */
export function HealthGauge({
  value = 82,
  size = 120,
  label = "HEALTH",
}: {
  value?: number | null;
  size?: number;
  label?: string;
}) {
  const reading =
    value !== null && Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : null;
  const geometry = gaugeGeometry(size);
  const color = gaugeColor(reading);
  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${String(size)} ${String(size)}`}
      role="img"
      aria-label={`${label}: ${String(reading ?? "UNKNOWN")}`}
    >
      <GaugeProgress {...{ geometry, reading, color }} />
      <GaugeTicks geometry={geometry} />
      <GaugeLabels {...{ geometry, reading, color, label }} />
    </svg>
  );
}

function GaugeProgress({
  geometry,
  reading,
  color,
}: {
  geometry: GaugeGeometry;
  reading: number | null;
  color: string;
}) {
  const { start, end } = geometry;
  return (
    <>
      <path
        d={gaugeArc(geometry, start, end)}
        fill="none"
        stroke="var(--bg-sunken)"
        strokeWidth="8"
        strokeLinecap="round"
      />
      {reading !== null && (
        <path
          d={gaugeArc(geometry, start, start + (reading / 100) * (end - start))}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
        />
      )}
    </>
  );
}

function GaugeLabels({
  geometry,
  reading,
  color,
  label,
}: {
  geometry: GaugeGeometry;
  reading: number | null;
  color: string;
  label: string;
}) {
  return (
    <>
      <text
        x={geometry.cx}
        y={geometry.cy - 4}
        textAnchor="middle"
        fontSize="24"
        fontFamily="var(--font-mono)"
        fontWeight="500"
        fill={color}
      >
        {reading ?? "—"}
      </text>
      <text
        x={geometry.cx}
        y={geometry.cy + 14}
        textAnchor="middle"
        fontSize="9"
        fontFamily="var(--font-mono)"
        fill="var(--fg-faint)"
        letterSpacing="0.1em"
      >
        {label}
      </text>
    </>
  );
}

function GaugeTicks({ geometry }: { geometry: GaugeGeometry }) {
  const { cx, cy, radius, start, end } = geometry;
  return (
    <>
      {[0, 25, 50, 75, 100].map((tick) => {
        const angle = start + (tick / 100) * (end - start);
        return (
          <line
            key={tick}
            x1={cx + (radius - 12) * Math.cos(angle)}
            y1={cy + (radius - 12) * Math.sin(angle)}
            x2={cx + (radius - 6) * Math.cos(angle)}
            y2={cy + (radius - 6) * Math.sin(angle)}
            stroke="var(--fg-faint)"
            strokeWidth="1"
          />
        );
      })}
    </>
  );
}
