import type * as E from "../../exampleTypes";
import { AVAILABLE_LANGUAGES } from "../availableLanguages";
import { Field } from "../Field";
import { EvaluationSectionSection } from "./EvaluationSectionSection";

interface EvaluationSectionField2Props {
  t: (key: string, fallback?: string) => string;
  ev: { benchmarks: string[]; languages: string[]; n_per_lang: number; temperature_grid: number[] };
  setP: E.UpdateProtocol;
}

export function EvaluationSectionField2({ t, ev, setP }: EvaluationSectionField2Props) {
  return (
    <Field
      label="evaluation.languages"
      tooltip={t("pe.ev.tip.languages")}
      hint={`${String(ev.languages.length)} ${t("pe.ev.langsSelected")} · ${String(
        AVAILABLE_LANGUAGES.length - ev.languages.length,
      )} ${t("pe.ev.langsMore")}`}
    >
      <EvaluationSectionSection {...{ ev, setP }} />
    </Field>
  );
}
