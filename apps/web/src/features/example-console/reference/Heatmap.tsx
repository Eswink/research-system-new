/** Reference: components/charts.jsx; EXAMPLE ONLY. */
export const Heatmap = ({
  data,
  xLabels = [],
  yLabels = [],
  cell = 14,
  gap = 2,
  color = "var(--accent)",
}: {
  data: number[][];
  xLabels?: string[];
  yLabels?: string[];
  cell?: number;
  gap?: number;
  color?: string;
}) => {
  const rows = data.length;
  const cols = data[0]?.length ?? 0;
  const w = cols * (cell + gap) + 40;
  const h = rows * (cell + gap) + 20;
  return <HeatmapChart {...{ w, h, yLabels, cell, gap, data, color, xLabels }} />;
};

interface HeatmapChartProps {
  w: number;
  h: number;
  yLabels: string[];
  cell: number;
  gap: number;
  data: number[][];
  color: string;
  xLabels: string[];
}

function HeatmapChart({ w, h, yLabels, cell, gap, data, color, xLabels }: HeatmapChartProps) {
  return (
    <svg width={w} height={h} viewBox={`0 0 ${String(w)} ${String(h)}`}>
      {yLabels.map((l, i) => (
        <text
          key={i}
          x={4}
          y={12 + i * (cell + gap) + cell / 1.4}
          fontSize="9"
          fontFamily="var(--font-mono)"
          fill="var(--fg-faint)"
        >
          {l}
        </text>
      ))}
      {data.map((row, y) =>
        row.map((v, x) => (
          <rect
            key={`${String(x)}-${String(y)}`}
            x={38 + x * (cell + gap)}
            y={4 + y * (cell + gap)}
            width={cell}
            height={cell}
            rx="2"
            fill={color}
            fillOpacity={0.1 + v * 0.9}
          />
        )),
      )}
      {xLabels.map((l, i) => (
        <text
          key={i}
          x={38 + i * (cell + gap) + cell / 2}
          y={h - 4}
          textAnchor="middle"
          fontSize="8"
          fontFamily="var(--font-mono)"
          fill="var(--fg-faint)"
        >
          {l}
        </text>
      ))}
    </svg>
  );
}
