import { type Dispatch, type SetStateAction } from "react";
import { EmptyState } from "../EmptyState";
import { Icon } from "../Icon";
import visual from "../LineageScreen.module.css";
import { LineageSection2 } from "./LineageSection2";

interface LineageEmptyTitleProps {
  selected: { id: string; label: string; kind: string } | undefined;
  kindIcons: Record<string, string>;
  kindColors: Record<string, string>;
  t: (key: string, fallback?: string) => string;
  upstream: string[];
  downstream: string[];
  nodes: { id: string; label: string; kind: string }[];
  setSelectedNode: Dispatch<SetStateAction<string>>;
}

export function LineageEmptyTitle({
  selected,
  kindIcons,
  kindColors,
  t,
  upstream,
  downstream,
  nodes,
  setSelectedNode,
}: LineageEmptyTitleProps) {
  return (
    <div className={`panel ${visual.panel2 ?? ""}`}>
      {selected ? (
        <>
          <div className={visual.surface2}>
            <div className={visual.row4}>
              <Icon
                name={kindIcons[selected.kind]}
                size={13}
                style={{ color: kindColors[selected.kind] }}
              />
              <span className={`mono ${visual.caption ?? ""}`}>{selected.kind}</span>
            </div>
            <div className={visual.label2}>{selected.label}</div>
            <div className={`mono ${visual.caption2 ?? ""}`}>{selected.id}</div>
          </div>
          <LineageSection2
            {...{ t, upstream, downstream, nodes, setSelectedNode, kindIcons, kindColors }}
          />
          <div className={visual.row8}>
            <button className={`btn sm ${visual.action ?? ""}`}>
              <Icon name="external" size={10} /> {t("ln.openNode")}
            </button>
            <button className="btn sm ghost">
              <Icon name="copy" size={10} />
            </button>
          </div>
        </>
      ) : (
        <EmptyState icon="graph" title={t("ln.emptyTitle")} description={t("ln.emptyDesc")} />
      )}
    </div>
  );
}
