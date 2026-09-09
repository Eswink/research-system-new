import { type Dispatch, type SetStateAction } from "react";
import { ForceGraph } from "../ForceGraph";
import { Icon } from "../Icon";
import visual from "../LineageScreen.module.css";

interface LineageSectionProps {
  t: (key: string, fallback?: string) => string;
  nodes: { id: string; label: string; kind: string }[];
  edges: { from: string; to: string }[];
  kindColors: Record<string, string>;
  kindIcons: Record<string, string>;
  graphNodes: { id: string; label: string; group: string; highlighted: boolean }[];
  setSelectedNode: Dispatch<SetStateAction<string>>;
  selectedNode: string;
}

export function LineageSection({
  t,
  nodes,
  edges,
  kindColors,
  kindIcons,
  graphNodes,
  setSelectedNode,
  selectedNode,
}: LineageSectionProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <span className={visual.label}>{t("ln.provGraph")}</span>
        <span className="chip">
          {nodes.length} {t("ln.nodes")}
        </span>
        <span className="chip">
          {edges.length} {t("ln.edges")}
        </span>
        <div className={visual.row2}>
          {Object.entries(kindColors).map(([k, c]) => (
            <span key={k} className={visual.row3}>
              <Icon name={kindIcons[k]} size={9} style={{ color: c }} />
              {t(`ln.kind.${k}`)}
            </span>
          ))}
        </div>
      </div>
      <div className={`canvas-bg ${visual.surface ?? ""}`}>
        <ForceGraph
          nodes={graphNodes}
          edges={edges}
          width={900}
          height={520}
          groupColors={kindColors}
          onNodeClick={(id) => {
            setSelectedNode(id);
          }}
          selectedId={selectedNode}
        />
      </div>
    </div>
  );
}
