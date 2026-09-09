import visual from "../BudgetScreen.module.css";
import { Icon } from "../Icon";

interface BudgetSection2Props {
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

export function BudgetSection2({ t, b }: BudgetSection2Props) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="diamond" size={12} className={visual.surface4} />
        <span className={visual.label}>{t("bg.reservations")}</span>
        <span className="chip">{b.reservations.length}</span>
      </div>
      <div className={visual.column2}>
        {b.reservations.map((r) => {
          const pct = r.used_minor / r.reserved_minor;
          const over = pct > 0.9;
          return (
            <div key={r.id}>
              <div className={visual.row2}>
                <span className={visual.surface5}>{r.label}</span>
                <span className={`mono ${visual.surface6 ?? ""}`}>
                  <span style={{ color: over ? "var(--warn)" : "var(--fg)" }}>
                    ${(r.used_minor / 100000).toFixed(2)}
                  </span>{" "}
                  / ${(r.reserved_minor / 100000).toFixed(2)}{" "}
                  <span className={visual.surface7}>· {(pct * 100).toFixed(0)}%</span>
                </span>
              </div>
              <div className={visual.indicator}>
                <div
                  className={visual.surface8}
                  style={{
                    width: `${String(Math.min(100, pct * 100))}%`,
                    background: over ? "var(--warn)" : "var(--accent)",
                  }}
                />
              </div>
            </div>
          );
        })}
        <div className={visual.label2}>
          <Icon name="q" size={10} />{" "}
          <strong>
            {b.unknown_cost_entries} {t("bg.unknownNote1")}
          </strong>{" "}
          <span className="mono">cost_status=UNKNOWN</span> {t("bg.unknownNote2")}
        </div>
      </div>
    </div>
  );
}
