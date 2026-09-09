import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { EvaluationSectionSecEvaluation } from "./evaluation-section/EvaluationDetails";
import { findErr } from "./findErr";

export const EvaluationSection = ({
  value,
  setP,
  errors,
  warnings = [],
}: E.ProtocolSectionProps) => {
  const { t } = useI18n();
  const ev = value.evaluation;
  const eN = findErr(errors, "evaluation.n_per_lang");
  const wN = findErr(warnings, "evaluation.n_per_lang");
  const wT = findErr(warnings, "evaluation.temperature_grid");
  return <EvaluationSectionSecEvaluation {...{ t, ev, setP, eN, wN, wT }} />;
};
