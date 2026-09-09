import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ExperimentDetail.module.css";
import { Icon } from "../Icon";
import { ExperimentDetailSection3 } from "./ExperimentDetailSection3";
import { ExperimentDetailSection4 } from "./ExperimentDetailSection4";

interface ExperimentDetailSection2Props {
  t: (key: string, fallback?: string) => string;
  totalRuns: number;
  e: FixtureTypes.Experiment;
}

export function ExperimentDetailSection2({ t, totalRuns, e }: ExperimentDetailSection2Props) {
  return (
    <div className={visual.column}>
      {/* Variable matrix */}
      <ExperimentDetailSection4 {...{ t, totalRuns, e }} />

      {/* Progress */}
      {e.status === "RUNNING" && (
        <div>
          <div className={visual.caption4}>{t("exp.progress")}</div>
          <div className={visual.indicator}>
            <div className={visual.indicator2} style={{ width: `${String(e.progress * 100)}%` }} />
          </div>
          <div className={visual.row6}>
            <span>
              {Math.round(e.progress * 100)}% · {Math.round(e.progress * totalRuns)} / {totalRuns}
            </span>
            <span>ETA {e.eta_min}m</span>
          </div>
        </div>
      )}

      {(e.failure_reason ?? e.paused_reason) && (
        <div className={visual.row7}>
          <Icon name="warn-tri" size={12} /> <div>{e.failure_reason ?? e.paused_reason}</div>
        </div>
      )}

      <div>
        <div className={visual.caption5}>{t("exp.meta").toUpperCase()}</div>
        <div className={visual.grid}>
          <span className={visual.surface2}>{t("lbl.project").toLowerCase()}</span>
          <span>{e.project_id}</span>
          <span className={visual.surface3}>{t("exp.submitted")}</span>
          <span>{new Date(e.submitted_at).toISOString().replace("T", " ").slice(0, 16)}</span>
          <span className={visual.surface4}>{t("exp.submittedBy")}</span>
          <span>{e.submitted_by}</span>
        </div>
      </div>

      <ExperimentDetailSection3 {...{ e, t }} />
    </div>
  );
}
