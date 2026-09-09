import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ExperimentMatrix.module.css";
import { ExperimentMatrixSection2 } from "./ExperimentMatrixSection2";

interface ExperimentMatrixSectionProps {
  t: (key: string, fallback?: string) => string;
  exp: FixtureTypes.Experiment;
  langs: string[];
  temps: number[];
  models: string[];
  status: (i: number, j: number, k: number) => "RUNNING" | "SUCCEEDED" | "FAILED" | "PENDING";
  color: (s: string) => "var(--success)" | "var(--accent)" | "var(--danger)" | "var(--bg-sunken)";
}

export function ExperimentMatrixSection({
  t,
  exp,
  langs,
  temps,
  models,
  status,
  color,
}: ExperimentMatrixSectionProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.surface}>
        <div className={visual.caption}>{t("exp.matrixTitle")}</div>
        <div className={visual.label}>{exp.label}</div>
        <div className={visual.label2}>{t("exp.matrixDesc")}</div>
      </div>

      <ExperimentMatrixSection2 {...{ langs, temps, models, status, color }} />

      {/* Legend */}
      <div className={visual.row2}>
        <span className={visual.row3}>
          <div className={visual.indicator} /> {t("exp.cellSucceeded")}
        </span>
        <span className={visual.row4}>
          <div className={visual.indicator2} /> {t("exp.cellRunning")}
        </span>
        <span className={visual.row5}>
          <div className={visual.indicator3} /> {t("exp.cellFailed")}
        </span>
        <span className={visual.row6}>
          <div className={visual.indicator4} /> {t("exp.cellPending")}
        </span>
      </div>
    </div>
  );
}
