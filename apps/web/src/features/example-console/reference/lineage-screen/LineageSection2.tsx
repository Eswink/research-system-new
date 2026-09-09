import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import visual from "../LineageScreen.module.css";
import { LineageSection3 } from "./LineageSection3";
import { LineageSection4 } from "./LineageSection4";

interface LineageSection2Props {
  t: (key: string, fallback?: string) => string;
  upstream: string[];
  downstream: string[];
  nodes: { id: string; label: string; kind: string }[];
  setSelectedNode: Dispatch<SetStateAction<string>>;
  kindIcons: Record<string, string>;
  kindColors: Record<string, string>;
}

export function LineageSection2({
  t,
  upstream,
  downstream,
  nodes,
  setSelectedNode,
  kindIcons,
  kindColors,
}: LineageSection2Props) {
  return (
    <div className={visual.column2}>
      {/* Impact stats */}
      <div className={visual.grid2}>
        <div className={visual.surface3}>
          <div className={visual.caption3}>{t("ln.upstream")}</div>
          <div className={visual.label3}>{upstream.length}</div>
        </div>
        <div className={visual.surface4}>
          <div className={visual.caption4}>{t("ln.downstream")}</div>
          <div className={visual.label4}>{downstream.length}</div>
        </div>
      </div>

      {/* Upstream list */}
      {upstream.length > 0 && (
        <div>
          <div className={visual.caption5}>{t("ln.upstreamDeps")}</div>
          <LineageSection3 {...{ upstream, nodes, setSelectedNode, kindIcons, kindColors }} />
        </div>
      )}

      {/* Downstream list */}
      {downstream.length > 0 && (
        <div>
          <div className={visual.caption7}>{t("ln.downstreamImpact")}</div>
          <LineageSection4 {...{ downstream, nodes, setSelectedNode, kindIcons, kindColors }} />
          <div className={visual.row7}>
            <Icon name="warn-tri" size={11} />
            {t("ln.impactWarn").replace("{n}", String(downstream.length))}
          </div>
        </div>
      )}
    </div>
  );
}
