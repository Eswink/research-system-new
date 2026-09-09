import visual from "../CostAnalyticsScreen.module.css";
import { Donut } from "../Donut";

interface CostAnalyticsSection6Props {
  totals: Record<string, number>;
  grandTotal: number;
  t: (key: string, fallback?: string) => string;
}

export function CostAnalyticsSection6({ totals, grandTotal, t }: CostAnalyticsSection6Props) {
  return (
    <div className={visual.row7}>
      <Donut
        values={Object.entries(totals).map(([k, v], i) => ({
          label: k,
          value: v,
          color:
            ["var(--accent)", "var(--success)", "var(--warn)", "var(--unknown)", "var(--danger)"][
              i
            ] ?? "var(--fg-muted)",
        }))}
        size={140}
        thickness={20}
        center={
          <>
            <div className={visual.label4}>${(grandTotal / 100).toFixed(0)}</div>
            <div className={visual.caption}>{t("ca.total")}</div>
          </>
        }
      />
      <div className={visual.column2}>
        {Object.entries(totals)
          .sort((a, b) => b[1] - a[1])
          .map(([k, v], i) => {
            const pct = ((v / grandTotal) * 100).toFixed(1);
            const color = [
              "var(--accent)",
              "var(--success)",
              "var(--warn)",
              "var(--unknown)",
              "var(--danger)",
            ][i];
            return (
              <div key={k} className={visual.row8}>
                <div className={visual.surface6} style={{ background: color }} />
                <span className={visual.surface7}>{k}</span>
                <span className={visual.surface8}>${(v / 100).toFixed(0)}</span>
                <span className={visual.surface9}>{pct}%</span>
              </div>
            );
          })}
      </div>
    </div>
  );
}
