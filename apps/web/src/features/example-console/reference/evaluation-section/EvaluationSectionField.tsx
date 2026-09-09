import type * as E from "../../exampleTypes";
import { Field } from "../Field";
import { EvaluationSectionSection2 } from "./EvaluationSectionSection2";

interface EvaluationSectionFieldProps {
  t: (key: string, fallback?: string) => string;
  eN: E.ProtocolIssue | undefined;
  wN: E.ProtocolIssue | undefined;
  setP: E.UpdateProtocol;
  ev: { benchmarks: string[]; languages: string[]; n_per_lang: number; temperature_grid: number[] };
}

export function EvaluationSectionField({ t, eN, wN, setP, ev }: EvaluationSectionFieldProps) {
  return (
    <Field
      label="evaluation.n_per_lang"
      tooltip={t("pe.ev.tip.n")}
      error={eN}
      hint={wN ? wN.message : t("pe.ev.hint.n")}
    >
      <EvaluationSectionSection2 {...{ setP, ev, eN, wN }} />
    </Field>
  );
}
