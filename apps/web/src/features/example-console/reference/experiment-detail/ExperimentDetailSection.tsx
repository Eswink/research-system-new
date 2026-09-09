import type * as FixtureTypes from "../../fixtureTypes";
import { DigestText } from "../DigestText";
import visual from "../ExperimentDetail.module.css";
import { ExpStatusBadge } from "../ExpStatusBadge";
import { PriorityChip } from "../PriorityChip";
import { ExperimentDetailSection2 } from "./ExperimentDetailSection2";

interface ExperimentDetailSectionProps {
  t: (key: string, fallback?: string) => string;
  e: FixtureTypes.Experiment;
  totalRuns: number;
}

export function ExperimentDetailSection({ t, e, totalRuns }: ExperimentDetailSectionProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.surface}>
        <div className={visual.caption}>{t("exp.headExperiment")}</div>
        <div className={visual.label}>{e.label}</div>
        <div className={visual.row}>
          <ExpStatusBadge status={e.status} />
          <PriorityChip priority={e.priority} />
          <DigestText value={e.id} length={12} prefix={false} />
        </div>
      </div>

      <ExperimentDetailSection2 {...{ t, totalRuns, e }} />
    </div>
  );
}
