import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../CompareScreen.module.css";
import { Icon } from "../Icon";
import { CompareSection5 } from "./CompareSection5";

interface CompareSectionProps {
  t: (key: string, fallback?: string) => string;
  metricKeys: string[];
  selectedRuns: FixtureTypes.Run[];
  metricValues: (runIdx: number, key: string) => number | null;
  bestFor: (key: string) => number | null;
}

export function CompareSection({
  t,
  metricKeys,
  selectedRuns,
  metricValues,
  bestFor,
}: CompareSectionProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row4}>
        <Icon name="graph" size={12} />
        <span className={visual.label}>{t("cmp.metrics")}</span>
        <span className={`chip ${visual.surface2 ?? ""}`}>
          {metricKeys.length} {t("cmp.rows")}
        </span>
      </div>
      <CompareSection5 {...{ selectedRuns, t, metricKeys, metricValues, bestFor }} />
    </div>
  );
}
