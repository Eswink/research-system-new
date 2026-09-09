import type * as E from "../../exampleTypes";
import { Field } from "../Field";
import { SectionHeader } from "../SectionHeader";
import { TemperatureGrid } from "../TemperatureGrid";
import { EvaluationSectionField } from "./EvaluationSectionField";
import { EvaluationSectionField2 } from "./EvaluationSectionField2";
import { EvaluationSectionField3 } from "./EvaluationSectionField3";

interface EvaluationSectionSecEvaluationProps {
  t: (key: string, fallback?: string) => string;
  ev: { benchmarks: string[]; languages: string[]; n_per_lang: number; temperature_grid: number[] };
  setP: E.UpdateProtocol;
  eN: E.ProtocolIssue | undefined;
  wN: E.ProtocolIssue | undefined;
  wT: E.ProtocolIssue | undefined;
}

export function EvaluationSectionSecEvaluation({
  t,
  ev,
  setP,
  eN,
  wN,
  wT,
}: EvaluationSectionSecEvaluationProps) {
  return (
    <div>
      <SectionHeader
        title={t("pe.sec.evaluation")}
        subtitle={t("pe.sec.evaluationDesc")}
        extra={
          <span className="chip mono">
            n = {ev.languages.length * ev.n_per_lang * ev.temperature_grid.length}
          </span>
        }
      />

      {/* Benchmarks */}
      <EvaluationSectionField3 {...{ t, ev, setP }} />

      {/* Languages */}
      <EvaluationSectionField2 {...{ t, ev, setP }} />

      {/* n_per_lang */}
      <EvaluationSectionField {...{ t, eN, wN, setP, ev }} />

      {/* Temperature grid */}
      <Field
        label="evaluation.temperature_grid"
        tooltip={t("pe.ev.tip.temp")}
        hint={wT ? wT.message : t("pe.ev.hint.temp")}
      >
        <TemperatureGrid
          values={ev.temperature_grid}
          onChange={(arr) => {
            setP((p) => {
              p.evaluation.temperature_grid = arr;
            });
          }}
        />
      </Field>
    </div>
  );
}
