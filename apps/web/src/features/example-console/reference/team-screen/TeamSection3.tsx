import { type Dispatch, type SetStateAction } from "react";
import visual from "../TeamScreen.module.css";
import { TeamSection } from "./TeamSection";
import { TeamSection6 } from "./TeamSection6";

interface TeamSection3Props {
  t: (key: string, fallback?: string) => string;
  modelUsage: Record<string, string[]>;
  setSelectedAgent: Dispatch<SetStateAction<string | null>>;
  selectedAgent: string | null;
}

export function TeamSection3({
  t,
  modelUsage,
  setSelectedAgent,
  selectedAgent,
}: TeamSection3Props) {
  return (
    <div className={visual.grid2}>
      {/* Roles */}
      <TeamSection6 {...{ t }} />

      {/* Agent grid */}
      <TeamSection {...{ t, modelUsage, setSelectedAgent, selectedAgent }} />
    </div>
  );
}
