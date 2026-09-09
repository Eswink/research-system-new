import { type Dispatch, type SetStateAction } from "react";
import visual from "../CostAnalyticsScreen.module.css";
import { Icon } from "../Icon";
import { PageToolbar } from "../PageToolbar";
import { ViewSwitcher } from "../ViewSwitcher";
import { CostAnalyticsSection } from "./CostAnalyticsSection";
import { CostAnalyticsSection2 } from "./CostAnalyticsSection2";
import { CostAnalyticsSection5 } from "./CostAnalyticsSection5";
import { CostAnalyticsTotalSpend } from "./CostAnalyticsTotalSpend";

interface CostAnalyticsTitleProps {
  t: (key: string, fallback?: string) => string;
  range: string;
  setRange: Dispatch<SetStateAction<string>>;
  grandTotal: number;
  totals: Record<string, number>;
  setPivot: Dispatch<SetStateAction<string>>;
  pivot: string;
}

export function CostAnalyticsTitle({
  t,
  range,
  setRange,
  grandTotal,
  totals,
  setPivot,
  pivot,
}: CostAnalyticsTitleProps) {
  return (
    <div className={visual.column}>
      <PageToolbar title={t("ca.title")} subtitle={t("ca.subtitle")}>
        <ViewSwitcher
          value={range}
          onChange={setRange}
          views={[
            { value: "7d", label: "7d" },
            { value: "30d", label: "30d" },
            { value: "90d", label: "90d" },
          ]}
        />
        <button className="btn sm">
          <Icon name="external" size={11} /> {t("act.exportCsv")}
        </button>
      </PageToolbar>

      {/* Top metric strip */}
      <CostAnalyticsTotalSpend {...{ t, grandTotal }} />

      {/* Sankey */}
      <CostAnalyticsSection5 {...{ t }} />

      {/* Line chart + bar breakdown */}
      <CostAnalyticsSection2 {...{ t, totals, grandTotal }} />

      {/* Table pivot */}
      <CostAnalyticsSection {...{ t, setPivot, pivot, grandTotal }} />
    </div>
  );
}
