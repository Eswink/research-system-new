import { useId } from "react";
import { useI18n } from "../../i18n/useI18n";
import styles from "./ProvenanceGraph.module.css";
import { layoutProvenance, type ProvenanceModel, type ProvenanceNode } from "./provenanceModel";

export function ProvenanceGraph({
  model,
  selectedId,
  onSelect,
  query = "",
}: {
  model: ProvenanceModel;
  selectedId: string | null;
  onSelect: (node: ProvenanceNode) => void;
  query?: string;
}) {
  const { language } = useI18n();
  const layout = layoutProvenance(model);
  const needle = query.trim().toLocaleLowerCase();
  return <ProvenanceGraphViewport {...{ language, layout, model, selectedId, needle, onSelect }} />;
}

interface ProvenanceGraphViewportProps {
  language: string;
  layout: {
    nodes: {
      x: number;
      y: number;
      id: string;
      entityId: string;
      kind: "source" | "evidence" | "claim";
      label: string;
      status: string;
      fields: readonly (readonly [string, string])[];
    }[];
    width: number;
    height: number;
  };
  model: ProvenanceModel;
  selectedId: string | null;
  needle: string;
  onSelect: (node: ProvenanceNode) => void;
}

function ProvenanceGraphViewport({
  language,
  layout,
  model,
  selectedId,
  needle,
  onSelect,
}: ProvenanceGraphViewportProps) {
  return (
    <div
      className={styles.viewport}
      role="region"
      aria-label={
        language === "zh"
          ? "来源关系图：Tab 选择节点，Enter 查看详情"
          : "Provenance graph: Tab to a node, Enter for details"
      }
    >
      <ProvenanceGraphCanvas {...{ layout, model, selectedId, needle, onSelect }} />
    </div>
  );
}

interface ProvenanceGraphCanvasProps {
  layout: {
    nodes: {
      x: number;
      y: number;
      id: string;
      entityId: string;
      kind: "source" | "evidence" | "claim";
      label: string;
      status: string;
      fields: readonly (readonly [string, string])[];
    }[];
    width: number;
    height: number;
  };
  model: ProvenanceModel;
  selectedId: string | null;
  needle: string;
  onSelect: (node: ProvenanceNode) => void;
}

function ProvenanceGraphCanvas({
  layout,
  model,
  selectedId,
  needle,
  onSelect,
}: ProvenanceGraphCanvasProps) {
  return (
    <div className={styles.canvas} style={{ width: layout.width, height: layout.height }}>
      <div className={styles.headings}>
        <span>SOURCE REFERENCE</span>
        <span>EVIDENCE</span>
        <span>CLAIM</span>
      </div>
      <GraphEdges model={model} layout={layout} />
      {layout.nodes.map((node) => (
        <button
          key={node.id}
          type="button"
          className={styles.node}
          style={{ left: node.x, top: node.y }}
          data-kind={node.kind}
          aria-pressed={selectedId === node.id}
          data-match={
            needle === "" ||
            `${node.label} ${node.entityId} ${node.status}`.toLocaleLowerCase().includes(needle)
          }
          onClick={() => {
            onSelect(node);
          }}
          title={`${node.entityId} · ${node.status}`}
        >
          <span className={styles.kind}>
            {node.kind.toUpperCase()} · {node.status}
          </span>
          <strong>{node.label}</strong>
          <span className={styles.identifier}>{node.entityId}</span>
        </button>
      ))}
    </div>
  );
}

function GraphEdges({
  model,
  layout,
}: {
  model: ProvenanceModel;
  layout: ReturnType<typeof layoutProvenance>;
}) {
  const markerId = useId().replaceAll(":", "");
  const nodes = new Map(layout.nodes.map((node) => [node.id, node]));
  return (
    <svg className={styles.edges} width={layout.width} height={layout.height} aria-hidden="true">
      <defs>
        <marker
          id={markerId}
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth="5"
          markerHeight="5"
          orient="auto"
        >
          <path d="M 0 0 L 10 5 L 0 10 Z" fill="currentColor" />
        </marker>
      </defs>
      {model.edges.map((edge) => {
        const from = nodes.get(edge.from);
        const to = nodes.get(edge.to);
        if (from === undefined || to === undefined) return null;
        const x1 = from.x + 220,
          x2 = to.x,
          y1 = from.y + 34,
          y2 = to.y + 34;
        const midpoint = (x1 + x2) / 2;
        const d = ["M", x1, y1, "C", midpoint, y1, midpoint, y2, x2, y2].join(" ");
        return (
          <path key={edge.id} d={d} markerEnd={`url(#${markerId})`}>
            <title>
              {edge.label}
              {edge.strength === undefined ? "" : ` · ${String(edge.strength)}`}
            </title>
          </path>
        );
      })}
    </svg>
  );
}
