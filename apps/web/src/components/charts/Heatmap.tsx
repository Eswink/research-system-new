import { num } from "./fmt";

const AXIS_FONT = { fontSize: 9, fontFamily: "var(--font-mono)", fill: "var(--fg-faint)" } as const;

function HeatCells({
  data,
  cell,
  gap,
  color,
}: {
  data: readonly (readonly number[])[];
  cell: number;
  gap: number;
  color: string;
}) {
  return (
    <>
      {data.map((row, y) =>
        row.map((v, x) => (
          <rect
            key={`${num(x)}-${num(y)}`}
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
    </>
  );
}

/** 矩阵热力图（实验网格、状态矩阵）。 */
export function Heatmap({
  data,
  xLabels = [],
  yLabels = [],
  cell = 14,
  gap = 2,
  color = "var(--accent)",
}: {
  data: readonly (readonly number[])[];
  xLabels?: readonly string[];
  yLabels?: readonly string[];
  cell?: number;
  gap?: number;
  color?: string;
}) {
  const rows = data.length;
  const cols = data[0]?.length ?? 0;
  const w = cols * (cell + gap) + 40;
  const h = rows * (cell + gap) + 20;
  return (
    <svg width={w} height={h} viewBox={`0 0 ${num(w)} ${num(h)}`} aria-hidden="true">
      {yLabels.map((l, i) => (
        <text key={l} x={4} y={12 + i * (cell + gap) + cell / 1.4} {...AXIS_FONT}>
          {l}
        </text>
      ))}
      <HeatCells data={data} cell={cell} gap={gap} color={color} />
      {xLabels.map((l, i) => (
        <text
          key={l}
          x={38 + i * (cell + gap) + cell / 2}
          y={h - 4}
          textAnchor="middle"
          fontSize={8}
          fontFamily="var(--font-mono)"
          fill="var(--fg-faint)"
        >
          {l}
        </text>
      ))}
    </svg>
  );
}
