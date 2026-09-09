import type * as FixtureTypes from "../../fixtureTypes";
import { Icon } from "../Icon";
import visual from "../RunDiffView.module.css";
import { TrendBadge } from "../TrendBadge";
import { fmtVal } from "../fmtVal";
import { RunDiffViewSection } from "./RunDiffViewSection";
import { RunDiffViewSection3 } from "./RunDiffViewSection3";

interface RunDiffViewSection2Props {
  a: FixtureTypes.Run | undefined;
  b: FixtureTypes.Run | undefined;
  t: (key: string, fallback?: string) => string;
  diff: {
    a: { id: string; label: string };
    b: { id: string; label: string };
    metrics: { key: string; a: number; b: number; delta: number; better: boolean; unit: string }[];
    manifest_diff: (
      | { field: string; a: string; b: string; note: string }
      | { field: string; a: number; b: number; note: string }
    )[];
  };
}

export function RunDiffViewSection2({ a, b, t, diff }: RunDiffViewSection2Props) {
  if (a === undefined || b === undefined) {
    return <p role="status">{t("cmp.noRuns", "Select two available example runs to compare.")}</p>;
  }
  return (
    <div className={visual.column}>
      {/* Header */}
      <RunDiffViewSection {...{ a, b, t }} />
      <MetricDiffPanel diff={diff} t={t} />

      {/* Manifest diff */}
      <RunDiffViewSection3 {...{ t, diff }} />
    </div>
  );
}

function MetricDiffPanel({ diff, t }: Pick<RunDiffViewSection2Props, "diff" | "t">) {
  const improved = diff.metrics.filter((metric) => metric.better).length;
  return (
    <div className={`panel ${visual.panel2 ?? ""}`}>
      <div className={visual.row3}>
        <Icon name="graph" size={12} />
        <span className={visual.label2}>{t("rh.metricDiff")}</span>
        <span className="chip">
          {diff.metrics.length} {t("rh.metrics")}
        </span>
        <span className={visual.caption5}>
          {improved} {t("rh.improved")} · {diff.metrics.length - improved} {t("rh.regressed")}
        </span>
      </div>
      <div>
        {diff.metrics.map((metric) => (
          <MetricDiffRow key={metric.key} metric={metric} />
        ))}
      </div>
    </div>
  );
}

function MetricDiffRow({
  metric: m,
}: {
  metric: RunDiffViewSection2Props["diff"]["metrics"][number];
}) {
  const format = (value: number) =>
    `${m.delta > 0 ? "+" : "−"}${fmtVal(value, m.unit)
      .replace("$", "")
      .replace("ms", "")
      .replace("%", "")
      .trim()}`;
  return (
    <div className={visual.grid3}>
      <span className={`mono ${visual.label3 ?? ""}`}>{m.key}</span>
      <span className={visual.label4}>{fmtVal(m.a, m.unit)}</span>
      <span className={visual.surface6}>→</span>
      <span className={visual.label5}>{fmtVal(m.b, m.unit)}</span>
      <span className={visual.surface7}>
        <TrendBadge delta={m.delta} inverted={!m.better} format={format} />
      </span>
    </div>
  );
}
