import { MetricCard } from "../MetricCard";
import visual from "../SettingsScreen.module.css";

interface SettingsBPlanProps {
  t: (key: string, fallback?: string) => string;
}

export function SettingsBPlan({ t }: SettingsBPlanProps) {
  return (
    <div className={visual.grid2}>
      <MetricCard
        label={t("st.b.plan")}
        value="Enterprise"
        sub={<span>{t("st.b.planSub")}</span>}
      />
      <MetricCard
        label={t("st.b.thisMonth")}
        value="$12,480"
        sub={<span>67% {t("st.b.ofCap")}</span>}
        bar={0.67}
      />
      <MetricCard label={t("st.b.seats")} value="24 / 30" sub={<span>{t("st.b.seatsSub")}</span>} />
    </div>
  );
}
