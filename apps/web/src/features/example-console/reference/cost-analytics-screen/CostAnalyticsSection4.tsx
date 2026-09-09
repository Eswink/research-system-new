import visual from "../CostAnalyticsScreen.module.css";
import { Icon } from "../Icon";
import { CostAnalyticsSection6 } from "./CostAnalyticsSection6";

interface CostAnalyticsSection4Props {
  t: (key: string, fallback?: string) => string;
  totals: Record<string, number>;
  grandTotal: number;
}

export function CostAnalyticsSection4({ t, totals, grandTotal }: CostAnalyticsSection4Props) {
  return (
    <div className={`panel ${visual.panel3 ?? ""}`}>
      <div className={visual.row6}>
        <Icon name="hex" size={12} />
        <span className={visual.label3}>{t("ca.spendByModel")}</span>
      </div>
      <CostAnalyticsSection6 {...{ totals, grandTotal, t }} />
    </div>
  );
}
