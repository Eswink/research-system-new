import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import visual from "../LineageScreen.module.css";

interface LineageSection3Props {
  upstream: string[];
  nodes: { id: string; label: string; kind: string }[];
  setSelectedNode: Dispatch<SetStateAction<string>>;
  kindIcons: Record<string, string>;
  kindColors: Record<string, string>;
}

export function LineageSection3({
  upstream,
  nodes,
  setSelectedNode,
  kindIcons,
  kindColors,
}: LineageSection3Props) {
  return (
    <div className={visual.column3}>
      {upstream.map((id) => {
        const nn = nodes.find((x) => x.id === id);
        if (!nn) return null;
        return (
          <button
            key={id}
            onClick={() => {
              setSelectedNode(id);
            }}
            className={visual.row5}
          >
            <Icon name={kindIcons[nn.kind]} size={11} style={{ color: kindColors[nn.kind] }} />
            <span className={visual.label5}>{nn.label}</span>
            <span className={`mono ${visual.caption6 ?? ""}`}>{nn.kind}</span>
          </button>
        );
      })}
    </div>
  );
}
