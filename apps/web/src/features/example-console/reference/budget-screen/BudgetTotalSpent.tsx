import visual from "../BudgetScreen.module.css";
import { BudgetSection } from "./BudgetSection";
import { BudgetTotalSpent2 } from "./BudgetTotalSpent2";

interface BudgetTotalSpentProps {
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

export function BudgetTotalSpent({
  t,
  b,
  totalReserved,
  totalUsed,
  burnRate,
}: BudgetTotalSpentProps) {
  return (
    <div className={visual.column}>
      {/* Metric cards */}
      <BudgetTotalSpent2 {...{ t, b, totalReserved, totalUsed, burnRate }} />

      <BudgetSection {...{ t, b }} />
    </div>
  );
}
