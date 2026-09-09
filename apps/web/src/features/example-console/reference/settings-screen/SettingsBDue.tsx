import { Icon } from "../Icon";
import visual from "../SettingsScreen.module.css";
import { StatusBadge } from "../StatusBadge";

interface SettingsBDueProps {
  t: (key: string, fallback?: string) => string;
}

export function SettingsBDue({ t }: SettingsBDueProps) {
  return (
    <div className={`panel ${visual.panel5 ?? ""}`}>
      <div className={visual.caption6}>{t("st.b.invoices")}</div>
      <div className={visual.column6}>
        {[
          { period: "2026-08", amount: 12480, status: "current", due: "2026-09-15" },
          { period: "2026-07", amount: 11820, status: "paid", due: "2026-08-15" },
          { period: "2026-06", amount: 10940, status: "paid", due: "2026-07-15" },
        ].map((inv) => (
          <div key={inv.period} className={visual.grid3}>
            <span className="mono">{inv.period}</span>
            <span className={visual.surface6}>Enterprise · monthly</span>
            <span className="mono">${inv.amount.toLocaleString()}</span>
            {inv.status === "current" ? (
              <StatusBadge tone="warn" icon="clock" label={t("st.b.due")} size="sm" />
            ) : (
              <StatusBadge tone="success" icon="check" label={t("st.b.paid")} size="sm" filled />
            )}
            <button className="btn sm ghost">
              <Icon name="external" size={10} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
