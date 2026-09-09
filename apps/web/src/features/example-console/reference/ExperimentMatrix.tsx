import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { ExperimentMatrixSection } from "./experiment-matrix/ExperimentMatrixSection";

export const ExperimentMatrix = ({ experiments }: { experiments: E.Experiment[] }) => {
  const { t } = useI18n();
  // Focus on the RUNNING sweep as an example
  const exp = experiments.find((e) => e.status === "RUNNING") ?? experiments[0];
  if (!exp) return <div className="empty-mark">No example experiments</div>;
  const temps = exp.variables.temperature ?? [0.2];
  const models = exp.variables.model;
  const langs = exp.variables.language ?? ["en"];

  // deterministic cell status
  const status = (i: number, j: number, k: number) => {
    const rn = (Math.sin(i * 3 + j * 7 + k * 13) + 1) / 2;
    const done = Math.min(1, exp.progress + 0.1);
    if (rn < done * 0.7) return "SUCCEEDED";
    if (rn < done * 0.85) return "RUNNING";
    if (rn < done * 0.92) return "FAILED";
    return "PENDING";
  };
  const color = (s: string) =>
    s === "SUCCEEDED"
      ? "var(--success)"
      : s === "RUNNING"
        ? "var(--accent)"
        : s === "FAILED"
          ? "var(--danger)"
          : "var(--bg-sunken)";

  return <ExperimentMatrixSection {...{ t, exp, langs, temps, models, status, color }} />;
};
