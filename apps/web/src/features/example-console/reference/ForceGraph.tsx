import { useMemo } from "react";
import type { GraphEdge, GraphNode } from "../exampleTypes";
import { layoutGraph, type Point } from "../graphGeometry";

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
  width?: number;
  height?: number;
  groupColors?: Record<string, string>;
  onNodeClick?: (id: string) => void;
  selectedId?: string;
}

/** Native, deterministic rendering of the design's example lineage graph. */
export function ForceGraph(props: Props) {
  const { nodes, edges, width = 480, height = 320 } = props;
  const positions = useMemo(
    () => layoutGraph(nodes, edges, { width, height }),
    [nodes, edges, width, height],
  );
  return (
    <svg width={width} height={height} viewBox={`0 0 ${String(width)} ${String(height)}`}>
      {edges.map((edge, index) => {
        const a = positions.get(edge.from),
          b = positions.get(edge.to);
        if (!a || !b) return null;
        const active = edge.from === props.selectedId || edge.to === props.selectedId;
        return (
          <line
            key={index}
            x1={a.x}
            y1={a.y}
            x2={b.x}
            y2={b.y}
            stroke={active ? "var(--accent)" : "var(--border)"}
            strokeWidth={active ? 1.5 : 1}
          />
        );
      })}
      {nodes.map((node) => {
        const point = positions.get(node.id);
        return point ? <GraphDot key={node.id} node={node} point={point} options={props} /> : null;
      })}
    </svg>
  );
}

function GraphDot({ node, point, options }: { node: GraphNode; point: Point; options: Props }) {
  const selected = node.id === options.selectedId;
  const dim = Boolean(options.selectedId) && !selected && node.highlighted === false;
  const color = options.groupColors?.[node.group] ?? "var(--accent)";
  const activate = () => {
    options.onNodeClick?.(node.id);
  };
  return (
    <g
      transform={`translate(${String(point.x)} ${String(point.y)})`}
      role="button"
      tabIndex={0}
      aria-label={node.label}
      aria-pressed={selected}
      onClick={activate}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          activate();
        }
      }}
      style={{ cursor: options.onNodeClick ? "pointer" : "default", opacity: dim ? 0.35 : 1 }}
    >
      <circle
        r={selected ? 6 : 4}
        fill={color}
        stroke={selected ? "var(--fg)" : "var(--bg-panel)"}
        strokeWidth={selected ? 2 : 1.5}
      />
      <text
        x="8"
        y="3"
        fontSize="9"
        fontFamily="var(--font-mono)"
        fill={selected ? "var(--fg)" : "var(--fg-muted)"}
        fontWeight={selected ? 600 : 400}
      >
        {node.label}
      </text>
    </g>
  );
}
