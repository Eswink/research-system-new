import type * as E from "../../exampleTypes";
import visual from "../DatasetsScreen.module.css";
import { ForceGraph } from "../ForceGraph";

interface DatasetsSection5Props {
  nodes: { id: string; label: string; group: string }[];
  edges: E.GraphEdge[];
}

export function DatasetsSection5({ nodes, edges }: DatasetsSection5Props) {
  return (
    <div className={visual.surface19}>
      <ForceGraph
        nodes={nodes}
        edges={edges}
        width={440}
        height={300}
        groupColors={{
          root: "var(--fg-muted)",
          mid: "var(--accent)",
          leaf: "var(--success)",
        }}
      />
    </div>
  );
}
