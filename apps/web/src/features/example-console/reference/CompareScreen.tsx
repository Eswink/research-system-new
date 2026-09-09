import { useState, type Dispatch, type SetStateAction } from "react";
import FIX_RUN_DIFF from "../data/run-diff.json";
import FIX_RUNS_HISTORY from "../data/runs-history.json";
import { requiredExample } from "../requiredExample";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./CompareScreen.module.css";
import { ComparePickerTitle } from "./compare-screen/ComparePickerTitle";
import { CompareSection2 } from "./compare-screen/CompareSection2";
import { CompareSection4 } from "./compare-screen/CompareSection4";
import { CompareTitle } from "./compare-screen/CompareTitle";

function nextSelectedRuns(selected: string[], id: string): string[] {
  if (selected.includes(id)) {
    return selected.length > 1 ? selected.filter((value) => value !== id) : selected;
  }
  if (selected.length >= 4) return [...selected.slice(1), id];
  return [...selected, id];
}

function metricValue(runIndex: number, key: string): number | null {
  const metric = FIX_RUN_DIFF.metrics.find((entry) => entry.key === key);
  if (metric === undefined) return null;
  if (runIndex === 0) return metric.a;
  if (runIndex === 1) return metric.b;
  const jitter = 1 + (runIndex * 0.07 - 0.1);
  return +(metric.a * jitter).toFixed(metric.unit === "ms" || metric.unit === "count" ? 0 : 3);
}

function bestMetricValue(
  selectedRuns: (typeof FIX_RUNS_HISTORY)[number][],
  key: string,
): number | null {
  const metric = FIX_RUN_DIFF.metrics.find((entry) => entry.key === key);
  if (metric === undefined) return null;
  const values = selectedRuns
    .map((_, index) => metricValue(index, key))
    .filter((value) => value !== null);
  const lowerIsBetter = metric.delta < 0 === metric.better;
  return lowerIsBetter ? Math.min(...values) : Math.max(...values);
}

export const CompareScreen = () => {
  const { t } = useI18n();
  const allRuns = FIX_RUNS_HISTORY;
  const [selected, setSelected] = useState(() => [
    requiredExample(allRuns[0]).id,
    requiredExample(allRuns[1]).id,
  ]);
  const [hideUnchanged, setHideUnchanged] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);

  const selectedRuns = selected
    .map((id) => allRuns.find((r) => r.id === id))
    .filter((r) => r !== undefined);
  const base = selectedRuns[0];

  const toggleRun = (id: string) => {
    setSelected((previous) => nextSelectedRuns(previous, id));
  };
  const metricKeys = FIX_RUN_DIFF.metrics.map((m) => m.key);
  const bestFor = (key: string) => bestMetricValue(selectedRuns, key);

  const manifestFields = FIX_RUN_DIFF.manifest_diff;
  const visibleManifest = hideUnchanged
    ? manifestFields.filter((f) => f.note !== "unchanged")
    : manifestFields;
  return (
    <CompareScreenLayout
      {...{
        t,
        hideUnchanged,
        setHideUnchanged,
        setPickerOpen,
        selectedRuns,
        toggleRun,
        metricKeys,
        bestFor,
        manifestFields,
        visibleManifest,
        base,
        pickerOpen,
        allRuns,
        selected,
      }}
    />
  );
};

interface CompareScreenLayoutProps {
  t: (key: string, fallback?: string) => string;
  hideUnchanged: boolean;
  setHideUnchanged: Dispatch<SetStateAction<boolean>>;
  setPickerOpen: Dispatch<SetStateAction<boolean>>;
  selectedRuns: (typeof FIX_RUNS_HISTORY)[number][];
  toggleRun: (id: string) => void;
  metricKeys: string[];
  bestFor: (key: string) => number | null;
  manifestFields: typeof FIX_RUN_DIFF.manifest_diff;
  visibleManifest: typeof FIX_RUN_DIFF.manifest_diff;
  base: (typeof FIX_RUNS_HISTORY)[number] | undefined;
  pickerOpen: boolean;
  allRuns: typeof FIX_RUNS_HISTORY;
  selected: string[];
}

function CompareScreenLayout(props: CompareScreenLayoutProps) {
  return (
    <div className={visual.column}>
      <CompareTitle
        t={props.t}
        hideUnchanged={props.hideUnchanged}
        setHideUnchanged={props.setHideUnchanged}
        setPickerOpen={props.setPickerOpen}
        selectedRuns={props.selectedRuns}
      />

      <CompareSection4 selectedRuns={props.selectedRuns} toggleRun={props.toggleRun} />

      <CompareSection2
        {...{
          t: props.t,
          metricKeys: props.metricKeys,
          selectedRuns: props.selectedRuns,
          metricValues: metricValue,
          bestFor: props.bestFor,
          manifestFields: props.manifestFields,
          visibleManifest: props.visibleManifest,
          base: props.base,
        }}
      />

      <ComparePickerTitle
        pickerOpen={props.pickerOpen}
        setPickerOpen={props.setPickerOpen}
        t={props.t}
        allRuns={props.allRuns}
        selected={props.selected}
        toggleRun={props.toggleRun}
      />
    </div>
  );
}
