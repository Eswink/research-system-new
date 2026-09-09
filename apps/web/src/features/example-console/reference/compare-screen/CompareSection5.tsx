import FIX_RUN_DIFF from "../../data/run-diff.json";
import type * as FixtureTypes from "../../fixtureTypes";
import { requiredExample } from "../../requiredExample";
import visual from "../CompareScreen.module.css";
import { Icon } from "../Icon";
import { UnknownValue } from "../UnknownValue";
import { CompareSection7 } from "./CompareSection7";
import { CompareSection8 } from "./CompareSection8";

interface CompareSection5Props {
  selectedRuns: FixtureTypes.Run[];
  t: (key: string, fallback?: string) => string;
  metricKeys: string[];
  metricValues: (runIdx: number, key: string) => number | null;
  bestFor: (key: string) => number | null;
}

export function CompareSection5({
  selectedRuns,
  t,
  metricKeys,
  metricValues,
  bestFor,
}: CompareSection5Props) {
  return (
    <div className={visual.surface3}>
      {/* Header */}
      <CompareSection8 {...{ selectedRuns, t }} />
      {metricKeys.map((metricKey) => (
        <MetricCompareRow key={metricKey} {...{ metricKey, selectedRuns, metricValues, bestFor }} />
      ))}
    </div>
  );
}

interface MetricCompareRowProps {
  metricKey: string;
  selectedRuns: FixtureTypes.Run[];
  metricValues: (runIdx: number, key: string) => number | null;
  bestFor: (key: string) => number | null;
}

function MetricCompareRow(props: MetricCompareRowProps) {
  const meta = requiredExample(
    FIX_RUN_DIFF.metrics.find((metric) => metric.key === props.metricKey),
  );
  const values = props.selectedRuns.map((_, index) => props.metricValues(index, props.metricKey));
  const known = values.filter((value): value is number => value !== null);
  const best = props.bestFor(props.metricKey);
  const delta = known.length >= 2 ? (known[1] ?? 0) - (known[0] ?? 0) : null;
  return (
    <div
      className="row"
      style={{
        gridTemplateColumns: `1.4fr repeat(${String(props.selectedRuns.length)}, 1fr) 80px`,
      }}
    >
      <div className={`mono ${visual.label2 ?? ""}`}>{props.metricKey}</div>
      {values.map((value, index) => (
        <MetricValue key={index} {...{ value, best, known, meta }} />
      ))}
      <CompareSection7 {...{ delta, meta }} />
    </div>
  );
}

function MetricValue({
  value,
  best,
  known,
  meta,
}: {
  value: number | null;
  best: number | null;
  known: number[];
  meta: (typeof FIX_RUN_DIFF.metrics)[number];
}) {
  const isBest = value === best && known.filter((candidate) => candidate === best).length === 1;
  return (
    <div className={`mono ${visual.row5 ?? ""}`}>
      <span
        style={{ color: isBest ? "var(--success)" : "var(--fg)", fontWeight: isBest ? 500 : 400 }}
      >
        {formatMetricValue(value, meta.unit)}
      </span>
      {isBest && <Icon name="check" size={9} className={visual.surface4} />}
    </div>
  );
}

function formatMetricValue(value: number | null, unit: string) {
  if (value === null) return <UnknownValue />;
  if (unit === "$") return `$${value.toFixed(2)}`;
  if (unit === "ms") return `${String(Math.round(value))} ms`;
  if (unit === "rate") return `${(value * 100).toFixed(1)}%`;
  return value;
}
