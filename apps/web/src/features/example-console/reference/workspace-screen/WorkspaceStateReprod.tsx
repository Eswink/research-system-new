import { type Dispatch, type SetStateAction } from "react";
import FIX_EXPERIMENTS from "../../data/experiments.json";
import { Icon } from "../Icon";
import visual from "../WorkspaceScreen.module.css";
import { WorkspaceStateReprod4 } from "./WorkspaceStateReprod4";

interface WorkspaceStateReprodProps {
  t: (key: string, fallback?: string) => string;
  setSelectedExp: Dispatch<SetStateAction<string>>;
  selectedExp: string;
}

export function WorkspaceStateReprod({
  t,
  setSelectedExp,
  selectedExp,
}: WorkspaceStateReprodProps) {
  return (
    <div className={`panel ${visual.panel2 ?? ""}`}>
      <div className={visual.row2}>
        <Icon name="flask" size={12} className={visual.surface3} />
        <span className={visual.label3}>{t("ws.experimentRuns")}</span>
        <span className="chip">{FIX_EXPERIMENTS.length}</span>
        <span className={visual.label4}>
          <span className={visual.surface4}>3 {t("ws.reproducible")}</span> ·{" "}
          <span className={visual.surface5}>1 {t("ws.notReproducible")}</span>
        </span>
      </div>
      <WorkspaceStateReprod4 {...{ t, setSelectedExp, selectedExp }} />
    </div>
  );
}
