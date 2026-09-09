import visual from "../BudgetScreen.module.css";
import { Icon } from "../Icon";
import { BudgetSection2 } from "./BudgetSection2";

interface BudgetSectionProps {
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

export function BudgetSection({ t, b }: BudgetSectionProps) {
  return (
    <div className={visual.grid2}>
      {/* Reservations */}
      <BudgetSection2 {...{ t, b }} />

      {/* Attribution by model */}
      <div className={`panel ${visual.panel2 ?? ""}`}>
        <div className={visual.row3}>
          <Icon name="hex" size={12} className={visual.surface9} />
          <span className={visual.label3}>{t("bg.byModel")}</span>
        </div>
        <div className={visual.surface10}>
          {(() => {
            const total = b.entries_by_model.reduce((a, e) => a + e.cost_minor, 0);
            return b.entries_by_model
              .sort((a, b) => b.cost_minor - a.cost_minor)
              .map((e, i) => {
                const pct = e.cost_minor / total;
                return (
                  <div key={e.model_id} className={visual.surface11}>
                    <div className={visual.row4}>
                      <span className={visual.label4}>{e.label}</span>
                      <span className={visual.label5}>${(e.cost_minor / 100000).toFixed(2)}</span>
                    </div>
                    <div className={visual.indicator2}>
                      <div
                        className={visual.surface12}
                        style={{
                          width: `${String(pct * 100)}%`,
                          background: `hsl(${String(210 + i * 25)}, 60%, 55%)`,
                        }}
                      />
                    </div>
                    <div className={visual.caption}>
                      {(e.tokens / 1000000).toFixed(2)}M tokens · $
                      {((e.cost_minor / 100000 / (e.tokens / 1000)) * 100).toFixed(3)}/1K tok
                    </div>
                  </div>
                );
              });
          })()}
        </div>
      </div>
    </div>
  );
}
