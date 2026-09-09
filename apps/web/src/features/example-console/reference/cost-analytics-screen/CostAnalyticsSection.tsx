import { type Dispatch, type SetStateAction } from "react";
import FIX_BUDGET from "../../data/budget.json";
import FIX_PROJECTS from "../../data/projects.json";
import visual from "../CostAnalyticsScreen.module.css";
import { Sparkline } from "../Sparkline";
import { CostAnalyticsSection3 } from "./CostAnalyticsSection3";

interface CostAnalyticsSectionProps {
  t: (key: string, fallback?: string) => string;
  setPivot: Dispatch<SetStateAction<string>>;
  pivot: string;
  grandTotal: number;
}

interface CostEntry {
  label: string;
  cost_minor: number;
  tokens: number;
}

function costEntries(pivot: string): CostEntry[] {
  if (pivot === "model") return FIX_BUDGET.entries_by_model;
  if (pivot === "project") {
    return FIX_PROJECTS.slice(0, 4).map((project) => ({
      label: project.name,
      cost_minor: project.spent_minor,
      tokens: project.spent_minor * 30,
    }));
  }
  return [
    { label: "literature", cost_minor: 720000, tokens: 4200000 },
    { label: "experiments", cost_minor: 1240000, tokens: 6800000 },
    { label: "review", cost_minor: 620000, tokens: 1400000 },
    { label: "writeup", cost_minor: 240000, tokens: 800000 },
  ];
}

export function CostAnalyticsSection({
  t,
  setPivot,
  pivot,
  grandTotal,
}: CostAnalyticsSectionProps) {
  const entries = costEntries(pivot);
  return (
    <div className={`panel ${visual.panel4 ?? ""}`}>
      <CostAnalyticsSection3 {...{ t, setPivot, pivot }} />
      <div className={`row head ${visual.surface10 ?? ""}`}>
        <span>{pivot}</span>
        <span>{t("ca.requests")}</span>
        <span>{t("ca.tokens")}</span>
        <span>{t("ca.spend")}</span>
        <span>{t("ca.avg1k")}</span>
        <span>{t("ca.share")}</span>
        <span>{t("ca.trend7d")}</span>
      </div>
      {entries.map((entry, index) => (
        <CostAnalyticsRow key={index} {...{ entry, index, grandTotal }} />
      ))}
    </div>
  );
}

function CostAnalyticsRow({
  entry,
  index,
  grandTotal,
}: {
  entry: CostEntry;
  index: number;
  grandTotal: number;
}) {
  const share = entry.cost_minor / grandTotal;
  const trend = Array.from(
    { length: 7 },
    (_, offset) =>
      Math.sin(index * 2 + offset * 0.7) * 20 +
      (entry.cost_minor / 100000 / 30) * (1 + offset * 0.05),
  );
  return (
    <div className={`row ${visual.surface11 ?? ""}`}>
      <span className={visual.label6}>{entry.label}</span>
      <span className={`mono ${visual.label7 ?? ""}`}>
        {Math.round(entry.tokens / 1000).toLocaleString()}k
      </span>
      <span className={`mono ${visual.label8 ?? ""}`}>
        {Math.round(entry.tokens / 1000).toLocaleString()}k
      </span>
      <span className={`mono ${visual.label9 ?? ""}`}>
        ${(entry.cost_minor / 100000).toFixed(2)}
      </span>
      <span className={`mono ${visual.label10 ?? ""}`}>
        ${(((entry.cost_minor / entry.tokens) * 1000) / 100).toFixed(3)}
      </span>
      <span>
        <div className={visual.row11}>
          <div className={visual.indicator4}>
            <div
              className={visual.indicator5}
              style={{ width: `${String(Math.min(share, 100))}%` }}
            />
          </div>
          <span className={`mono ${visual.caption2 ?? ""}`}>{share.toFixed(1)}%</span>
        </div>
      </span>
      <span>
        <Sparkline data={trend} width={100} height={22} />
      </span>
    </div>
  );
}
