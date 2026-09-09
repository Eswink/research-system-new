import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import visual from "../LineageScreen.module.css";

interface LineageSection4Props {
  downstream: string[];
  nodes: { id: string; label: string; kind: string }[];
  setSelectedNode: Dispatch<SetStateAction<string>>;
  kindIcons: Record<string, string>;
  kindColors: Record<string, string>;
}

export function LineageSection4({
  downstream,
  nodes,
  setSelectedNode,
  kindIcons,
  kindColors,
}: LineageSection4Props) {
  return (
    <div className={visual.column4}>
      {downstream.map((id) => {
        const nn = nodes.find((x) => x.id === id);
        if (!nn) return null;
        return (
          <button
            key={id}
            onClick={() => {
              setSelectedNode(id);
            }}
            className={visual.row6}
          >
            <Icon name={kindIcons[nn.kind]} size={11} style={{ color: kindColors[nn.kind] }} />
            <span className={visual.label6}>{nn.label}</span>
            <span className={`mono ${visual.caption8 ?? ""}`}>{nn.kind}</span>
          </button>
        );
      })}
    </div>
  );
}
