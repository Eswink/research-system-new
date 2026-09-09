import FIX_BUDGET from "../../data/budget.json";
import FIX_COST_DAILY from "../../data/cost-daily.json";
import visual from "../CostAnalyticsScreen.module.css";
import { MetricCard } from "../MetricCard";

interface CostAnalyticsTotalSpendProps {
  t: (key: string, fallback?: string) => string;
  grandTotal: number;
}

export function CostAnalyticsTotalSpend({ t, grandTotal }: CostAnalyticsTotalSpendProps) {
  return (
    <div className={visual.grid}>
      <MetricCard
        label={t("ca.totalSpend")}
        value={`$${(grandTotal / 100).toFixed(2)}`}
        sub={<span>{t("ca.totalSpendSub")}</span>}
        trend={12.4}
      />
      <MetricCard
        label={t("ca.avgDaily")}
        value={`$${(grandTotal / 30 / 100).toFixed(2)}`}
        sub={
          <span>
            {t("ca.avgDailyProj")}{" "}
            <span className="mono">${((grandTotal / 100) * 1.03).toFixed(0)}</span>
          </span>
        }
        spark={FIX_COST_DAILY.map((d) =>
          Object.values(d)
            .filter((v) => typeof v === "number")
            .reduce((a, b) => a + b, 0),
        )}
      />
      <MetricCard
        label={t("ca.unknownCost")}
        value={<span className={visual.surface}>{FIX_BUDGET.unknown_cost_entries}</span>}
        sub={
          <span className={visual.surface2}>
            {t("ca.unknownCostSub")} <span className="mono">cost_status=UNKNOWN</span>
          </span>
        }
        unknownWarn
      />
      <MetricCard
        label={t("ca.topModel")}
        value="Opus 4.1"
        sub={
          <span>
            $1,104 · <span className={`mono ${visual.surface3 ?? ""}`}>35.4%</span>{" "}
            {t("ca.topModelSub")}
          </span>
        }
      />
    </div>
  );
}
