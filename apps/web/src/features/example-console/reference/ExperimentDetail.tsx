import { useMemo } from "react";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { ExperimentDetailSection } from "./experiment-detail/ExperimentDetailSection";

export const ExperimentDetail = ({ experiment: e }: { experiment: E.Experiment }) => {
  const { t } = useI18n();
  const totalRuns = useMemo(() => {
    return Object.values(e.variables).reduce<number>(
      (acc, v) => acc * (Array.isArray(v) ? v.length : 1),
      1,
    );
  }, [e]);

  return <ExperimentDetailSection {...{ t, e, totalRuns }} />;
};
