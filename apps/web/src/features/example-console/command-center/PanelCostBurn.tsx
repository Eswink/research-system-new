import FIX_COST_DAILY from "../data/cost-daily.json";
import { LineSeries } from "../reference/LineSeries";
import { Panel } from "./Panel";
import visual from "./PanelCostBurn.module.css";

const COST_MODELS = ["gpt-4o", "opus-4.1", "gemini-2.5"] as const;

/** Reference: Command Center.html; every metric is a fixed example. */
export const PanelCostBurn = () => (
  <Panel
    kicker="BUDGET"
    title="Burn Rate · 30d"
    right={<span className={visual.caption}>62% USED</span>}
    className={visual.surface}
  >
    <div className={visual.surface2}>
      <div className={visual.row}>
        <span className={visual.label}>$3,120</span>
        <span className={visual.label2}>/ $5,000 cap</span>
        <span className={visual.caption2}>▲ +$492/hr · breach in ~29m</span>
      </div>
    </div>
    <LineSeries
      data={COST_MODELS.map((m) => ({
        label: m,
        values: FIX_COST_DAILY.slice(-14).map((d) => Math.round(d[m] / 100)),
      }))}
      colors={["var(--accent)", "var(--warn)", "var(--unknown)"]}
      xLabels={FIX_COST_DAILY.slice(-14).map((d, i) => (i % 3 === 0 ? d.date.slice(5) : ""))}
      width={480}
      height={140}
    />
  </Panel>
);
