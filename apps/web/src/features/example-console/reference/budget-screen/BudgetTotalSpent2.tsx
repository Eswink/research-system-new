import { MetricCard } from "../BudgetMetricCard";
import visual from "../BudgetScreen.module.css";
import { BudgetTotalSpent3 } from "./BudgetTotalSpent3";

interface BudgetTotalSpent2Props {
  t: (key: string, fallback?: string) => string;
  b: {
    total_estimated_cost_minor: number;
    actual_cost_minor: number;
    unknown_cost_entries: number;
    budget_cap_minor: number;
    reservations: { id: string; label: string; reserved_minor: number; used_minor: number }[];
    entries_by_model: { model_id: string; label: string; cost_minor: number; tokens: number }[];
  };
  totalReserved: number;
  totalUsed: number;
  burnRate: number;
}

export function BudgetTotalSpent2({
  t,
  b,
  totalReserved,
  totalUsed,
  burnRate,
}: BudgetTotalSpent2Props) {
  return (
    <div className={visual.grid}>
      <BudgetTotalSpent3 {...{ t, b }} />
      <MetricCard
        label={t("bg.reserved")}
        value={`$${(totalReserved / 100000).toFixed(2)}`}
        sub={
          <span>
            <span className="mono">${(totalUsed / 100000).toFixed(2)}</span> {t("bg.reservedOf")} (
            {((totalUsed / totalReserved) * 100).toFixed(0)}%)
          </span>
        }
        bar={totalUsed / totalReserved}
        barColor="var(--success)"
      />
      <MetricCard
        label={t("bg.unknown")}
        value={<span className={visual.surface}>{b.unknown_cost_entries}</span>}
        sub={
          <span className={visual.surface2}>
            {t("bg.unknownSub")} <span className="mono">cost_status=UNKNOWN</span>
          </span>
        }
        unknownWarn
      />
      <MetricCard
        label={t("bg.burn")}
        value={`$${((burnRate / 100000) * 60).toFixed(2)}/hr`}
        sub={
          <span>
            {t("bg.burnProj")}{" "}
            <span className={`mono ${visual.surface3 ?? ""}`}>{t("bg.burnEta")}</span>
          </span>
        }
        bar={0.86}
        barColor="var(--warn)"
      />
    </div>
  );
}
