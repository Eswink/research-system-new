import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ExperimentDetail.module.css";

interface ExperimentDetailSection4Props {
  t: (key: string, fallback?: string) => string;
  totalRuns: number;
  e: FixtureTypes.Experiment;
}

export function ExperimentDetailSection4({ t, totalRuns, e }: ExperimentDetailSection4Props) {
  return (
    <div>
      <div className={visual.row2}>
        <div className={visual.caption2}>{t("exp.variables")}</div>
        <span className="chip">
          {totalRuns} {t("exp.cartesian")}
        </span>
      </div>
      <div className={visual.column2}>
        {Object.entries(e.variables).map(([k, v]) => (
          <div key={k} className={visual.row3}>
            <span className={visual.label2}>{k}</span>
            <div className={visual.row4}>
              {(Array.isArray(v) ? v : [v]).map((val, i) => (
                <span key={i} className={visual.row5}>
                  {String(val)}
                </span>
              ))}
            </div>
            <span className={visual.caption3}>× {Array.isArray(v) ? v.length : 1}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
