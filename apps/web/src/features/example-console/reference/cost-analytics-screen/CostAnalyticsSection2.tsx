import FIX_COST_DAILY from "../../data/cost-daily.json";
import visual from "../CostAnalyticsScreen.module.css";
import { Icon } from "../Icon";
import { LineSeries } from "../LineSeries";
import { CostAnalyticsSection4 } from "./CostAnalyticsSection4";

interface CostAnalyticsSection2Props {
  t: (key: string, fallback?: string) => string;
  totals: Record<string, number>;
  grandTotal: number;
}

export function CostAnalyticsSection2({ t, totals, grandTotal }: CostAnalyticsSection2Props) {
  return (
    <div className={visual.grid2}>
      <div className={`panel ${visual.panel2 ?? ""}`}>
        <div className={visual.row3}>
          <Icon name="graph" size={12} />
          <span className={visual.label2}>{t("ca.daily")}</span>
          <span className="chip">{t("ca.last30d")}</span>
        </div>
        <LineSeries
          data={(["gpt-4o", "sonnet-4", "opus-4.1", "gemini-2.5", "qwen3-235b"] as const).map(
            (m) => ({
              label: m,
              values: FIX_COST_DAILY.map((d) => Math.round(d[m] / 100)),
            }),
          )}
          xLabels={FIX_COST_DAILY.map((d, i) => (i % 5 === 0 ? d.date.slice(5) : "")).filter(
            (x, i) => i % 5 === 0,
          )}
          width={720}
          height={220}
          yFormat={(v) => `$${String(v)}`}
        />
        <div className={visual.row4}>
          {(
            [
              ["gpt-4o", "var(--accent)"],
              ["sonnet-4", "var(--success)"],
              ["opus-4.1", "var(--warn)"],
              ["gemini-2.5", "var(--unknown)"],
              ["qwen3-235b", "var(--danger)"],
            ] as const
          ).map(([n, c]) => (
            <span key={n} className={visual.row5}>
              <div className={visual.surface5} style={{ background: c }} /> {n}
            </span>
          ))}
        </div>
      </div>

      <CostAnalyticsSection4 {...{ t, totals, grandTotal }} />
    </div>
  );
}
