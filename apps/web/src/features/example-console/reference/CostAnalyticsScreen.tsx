import { useMemo, useState } from "react";
import FIX_COST_DAILY from "../data/cost-daily.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { CostAnalyticsTitle } from "./cost-analytics-screen/CostAnalyticsTitle";

export const CostAnalyticsScreen = () => {
  const { t } = useI18n();
  const [pivot, setPivot] = useState("model"); // model | project | task
  const [range, setRange] = useState("30d");

  // Compute totals from COST_DAILY
  const totals = useMemo(() => {
    const t: Record<string, number> = {};
    FIX_COST_DAILY.forEach((row) => {
      Object.entries(row).forEach(([k, v]) => {
        if (typeof v !== "number") return;
        t[k] = (t[k] ?? 0) + v;
      });
    });
    return t;
  }, []);
  const grandTotal = Object.values(totals).reduce((a, b) => a + b, 0);

  return <CostAnalyticsTitle {...{ t, range, setRange, grandTotal, totals, setPivot, pivot }} />;
};
