import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../CompareScreen.module.css";
import { CompareSection } from "./CompareSection";
import { CompareSection3 } from "./CompareSection3";

interface CompareSection2Props {
  t: (key: string, fallback?: string) => string;
  metricKeys: string[];
  selectedRuns: FixtureTypes.Run[];
  metricValues: (runIdx: number, key: string) => number | null;
  bestFor: (key: string) => number | null;
  manifestFields: (
    | { field: string; a: string; b: string; note: string }
    | { field: string; a: number; b: number; note: string }
  )[];
  visibleManifest: (
    | { field: string; a: string; b: string; note: string }
    | { field: string; a: number; b: number; note: string }
  )[];
  base: FixtureTypes.Run | undefined;
}

export function CompareSection2({
  t,
  metricKeys,
  selectedRuns,
  metricValues,
  bestFor,
  manifestFields,
  visibleManifest,
  base,
}: CompareSection2Props) {
  return (
    <div className={visual.grid}>
      {/* Metrics matrix */}
      <CompareSection {...{ t, metricKeys, selectedRuns, metricValues, bestFor }} />

      {/* Manifest + summary */}
      <CompareSection3 {...{ t, manifestFields, visibleManifest, base, selectedRuns }} />
    </div>
  );
}
