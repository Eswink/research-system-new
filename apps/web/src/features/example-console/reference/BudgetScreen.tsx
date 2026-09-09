import FIX_BUDGET from "../data/budget.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { BudgetTotalSpent } from "./budget-screen/BudgetTotalSpent";

export const BudgetScreen = () => {
  const { t } = useI18n();
  const b = FIX_BUDGET;
  const burnRate = 3120000 / 38; // $ minor / min
  const totalReserved = b.reservations.reduce((a, r) => a + r.reserved_minor, 0);
  const totalUsed = b.reservations.reduce((a, r) => a + r.used_minor, 0);

  return <BudgetTotalSpent {...{ t, b, totalReserved, totalUsed, burnRate }} />;
};
