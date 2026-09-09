import FIX_COST_SANKEY from "../../data/cost-sankey.json";
import visual from "../CostAnalyticsScreen.module.css";
import { Icon } from "../Icon";
import { Sankey } from "../Sankey";

interface CostAnalyticsSection5Props {
  t: (key: string, fallback?: string) => string;
}

export function CostAnalyticsSection5({ t }: CostAnalyticsSection5Props) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="graph" size={12} />
        <span className={visual.label}>{t("ca.flow")}</span>
        <span className="chip">sankey</span>
        <div className={visual.row2}>
          <span>
            <div className={visual.indicator} />
            {t("ca.legendProject")}
          </span>
          <span>
            <div className={visual.indicator2} />
            {t("ca.legendModel")}
          </span>
          <span>
            <div className={visual.indicator3} />
            {t("ca.legendTask")}
          </span>
        </div>
      </div>
      <div className={visual.surface4}>
        <Sankey
          nodes={FIX_COST_SANKEY.nodes}
          flows={FIX_COST_SANKEY.flows}
          width={880}
          height={360}
        />
      </div>
    </div>
  );
}
