import FIX_BUDGET from "../../data/budget.json";
import visual from "../DryRunScreen.module.css";
import { Icon } from "../Icon";
import { UnknownValue } from "../UnknownValue";
import { ZoneHeader } from "../ZoneHeader";
import { fmtMinor } from "../fmtMinor";
import { isBlocked, type ExamplePreflight } from "../preflightModel";

interface DryRunBudgetProjProps {
  t: (key: string, fallback?: string) => string;
  preflight: ExamplePreflight;
}

export function DryRunBudgetProj({ t, preflight }: DryRunBudgetProjProps) {
  const blocked = isBlocked(preflight);
  return (
    <section className="panel">
      <ZoneHeader
        icon="diamond"
        title={t("dr.budgetProj")}
        extra={
          blocked ? (
            <UnknownValue hint={t("dr.budgetUnknown")} />
          ) : (
            <span className={`mono ${visual.label6 ?? ""}`}>
              {fmtMinor(preflight.estimated_cost_minor)} / {fmtMinor(5000000)}
            </span>
          )
        }
      />
      {blocked ? (
        <div className={visual.row6}>
          <Icon name="q" size={12} /> {t("dr.budgetFail")}
        </div>
      ) : (
        <div className={visual.surface10}>
          {FIX_BUDGET.reservations.map((r) => (
            <div key={r.id} className={visual.grid3}>
              <span className={visual.surface11}>{r.label}</span>
              <div className={visual.indicator}>
                <div
                  className={visual.indicator2}
                  style={{
                    width: `${String(Math.min(100, (r.used_minor / r.reserved_minor) * 100))}%`,
                  }}
                />
              </div>
              <span className={`mono ${visual.label7 ?? ""}`}>
                {fmtMinor(r.used_minor)} / {fmtMinor(r.reserved_minor)}
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
