import type { SankeyFlow, SankeyNode } from "../exampleTypes";
import { layoutSankey, sankeyPaths } from "../sankeyGeometry";

interface Props {
  nodes: SankeyNode[];
  flows: SankeyFlow[];
  width?: number;
  height?: number;
}

/** Reference: components/charts.jsx; example costs never enter the real UsageLedger. */
export function Sankey({ nodes, flows, width = 640, height = 320 }: Props) {
  const positions = layoutSankey(nodes, flows, { width, height });
  const paths = sankeyPaths(flows, positions);
  return (
    <svg width={width} height={height} viewBox={`0 0 ${String(width)} ${String(height)}`}>
      {paths.map((path) => (
        <path
          key={path.index}
          d={path.d}
          fill="none"
          stroke="var(--accent)"
          strokeOpacity="0.18"
          strokeWidth={path.width}
          strokeLinecap="butt"
        />
      ))}
      {nodes.map((node) => {
        const p = positions.get(node.id);
        if (!p) return null;
        const color =
          node.type === "project"
            ? "var(--fg-muted)"
            : node.type === "task"
              ? "var(--success)"
              : "var(--accent)";
        return (
          <g key={node.id}>
            <rect x={p.x} y={p.y} width="8" height={p.h} rx="2" fill={color} />
            <text
              x={p.x + 14}
              y={p.y + p.h / 2 + 3}
              fontSize="10"
              fontFamily="var(--font-mono)"
              fill="var(--fg)"
              opacity="0.9"
            >
              {node.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
