import { MetricCard } from "../BudgetMetricCard";

interface BudgetTotalSpent3Props {
  t: (key: string, fallback?: string) => string;
  b: {
    total_estimated_cost_minor: number;
    actual_cost_minor: number;
    unknown_cost_entries: number;
    budget_cap_minor: number;
    reservations: { id: string; label: string; reserved_minor: number; used_minor: number }[];
    entries_by_model: { model_id: string; label: string; cost_minor: number; tokens: number }[];
  };
}

export function BudgetTotalSpent3({ t, b }: BudgetTotalSpent3Props) {
  return (
    <MetricCard
      label={t("bg.totalSpent")}
      value={`$${(b.actual_cost_minor / 100000).toFixed(2)}`}
      sub={
        <span>
          of <span className="mono">${(b.budget_cap_minor / 100000).toFixed(2)}</span> cap ·{" "}
          {((b.actual_cost_minor / b.budget_cap_minor) * 100).toFixed(1)}%
        </span>
      }
      bar={b.actual_cost_minor / b.budget_cap_minor}
      barColor="var(--accent)"
    />
  );
}
