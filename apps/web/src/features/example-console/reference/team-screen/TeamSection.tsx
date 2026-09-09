import { type Dispatch, type SetStateAction } from "react";
import FIX_AGENTS from "../../data/agents.json";
import { Icon } from "../Icon";
import visual from "../TeamScreen.module.css";
import { TeamSection4 } from "./TeamSection4";

interface TeamSectionProps {
  t: (key: string, fallback?: string) => string;
  modelUsage: Record<string, string[]>;
  setSelectedAgent: Dispatch<SetStateAction<string | null>>;
  selectedAgent: string | null;
}

export function TeamSection({ t, modelUsage, setSelectedAgent, selectedAgent }: TeamSectionProps) {
  return (
    <div className={`panel ${visual.panel3 ?? ""}`}>
      <div className={visual.row7}>
        <Icon name="graph" size={12} className={visual.surface7} />
        <span className={visual.label5}>{t("tm.agents")}</span>
        <span className="chip">{FIX_AGENTS.length}</span>
        <div className={visual.row8}>
          <Icon name="warn-tri" size={11} /> {t("tm.hetConflict")}
        </div>
      </div>
      <TeamSection4 {...{ modelUsage, setSelectedAgent, selectedAgent, t }} />
    </div>
  );
}
