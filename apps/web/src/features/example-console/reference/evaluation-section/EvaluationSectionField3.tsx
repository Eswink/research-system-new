import type * as E from "../../exampleTypes";
import { AVAILABLE_BENCHMARKS } from "../availableBenchmarks";
import { ChipMultiSelect } from "../ChipMultiSelect";
import { Field } from "../Field";

interface EvaluationSectionField3Props {
  t: (key: string, fallback?: string) => string;
  ev: { benchmarks: string[]; languages: string[]; n_per_lang: number; temperature_grid: number[] };
  setP: E.UpdateProtocol;
}

export function EvaluationSectionField3({ t, ev, setP }: EvaluationSectionField3Props) {
  return (
    <Field label="evaluation.benchmarks" tooltip={t("pe.ev.tip.benchmarks")}>
      <ChipMultiSelect
        items={ev.benchmarks}
        available={AVAILABLE_BENCHMARKS}
        onAdd={(v) => {
          setP((p) => {
            if (!p.evaluation.benchmarks.includes(v)) p.evaluation.benchmarks.push(v);
          });
        }}
        onRemove={(v) => {
          setP((p) => {
            p.evaluation.benchmarks = p.evaluation.benchmarks.filter((x) => x !== v);
          });
        }}
        onFreeAdd={(v) => {
          setP((p) => {
            if (v && !p.evaluation.benchmarks.includes(v)) p.evaluation.benchmarks.push(v);
          });
        }}
      />
    </Field>
  );
}
