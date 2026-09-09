import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./StepModels.module.css";

/** Reference: screens/Setup.jsx; EXAMPLE ONLY. */
export const StepModels = () => {
  const { t } = useI18n();
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.label}>{t("st.models.title")}</div>
      <div className={visual.label2}>{t("st.models.desc")}</div>
      <div className={visual.surface}>
        {(
          [
            ["claude-opus-4-1-20250805", true, "Frontier · 200k ctx"],
            ["claude-sonnet-4-20250514", true, "Balanced · 200k ctx"],
            ["claude-3-5-haiku-20241022", true, "Fast · 200k ctx"],
            ["claude-3-opus-20240229", false, "Legacy · 200k ctx"],
            ["claude-3-sonnet-20240229", false, "Legacy · 200k ctx"],
          ] as const
        ).map(([id, checked, hint], i) => (
          <label
            key={id}
            className={visual.grid}
            style={{ borderBottom: i < 4 ? "1px solid var(--border-subtle)" : "none" }}
          >
            <input type="checkbox" defaultChecked={checked} className={visual.field} />
            <span className={`mono ${visual.label3 ?? ""}`}>{id}</span>
            <span className={visual.label4}>{hint}</span>
          </label>
        ))}
      </div>
    </div>
  );
};
