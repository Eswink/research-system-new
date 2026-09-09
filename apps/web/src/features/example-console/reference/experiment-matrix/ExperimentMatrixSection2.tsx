import visual from "../ExperimentMatrix.module.css";
import { ExperimentMatrixSection3 } from "./ExperimentMatrixSection3";

interface ExperimentMatrixSection2Props {
  langs: string[];
  temps: number[];
  models: string[];
  status: (i: number, j: number, k: number) => "RUNNING" | "SUCCEEDED" | "FAILED" | "PENDING";
  color: (s: string) => "var(--success)" | "var(--accent)" | "var(--danger)" | "var(--bg-sunken)";
}

export function ExperimentMatrixSection2({
  langs,
  temps,
  models,
  status,
  color,
}: ExperimentMatrixSection2Props) {
  return (
    <div className={visual.column}>
      {langs.map((lang, li) => (
        <div key={lang}>
          <div className={visual.label3}>language · {lang}</div>
          <ExperimentMatrixSection3 {...{ temps, models, status, li, lang, color }} />
        </div>
      ))}
    </div>
  );
}
