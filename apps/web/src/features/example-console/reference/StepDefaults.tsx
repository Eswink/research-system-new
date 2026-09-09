import { useExampleI18n as useI18n } from "../useExampleI18n";
import { INPUT } from "./setupInput";
import visual from "./StepDefaults.module.css";

/** Reference: screens/Setup.jsx; EXAMPLE ONLY. */
export const StepDefaults = () => {
  const { t } = useI18n();
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.label}>{t("st.def.title")}</div>
      <div className={visual.label2}>{t("st.def.desc")}</div>
      {(
        [
          ["fast_retrieval", "claude-3-5-haiku-20241022"],
          ["balanced_reasoning", "claude-sonnet-4-20250514"],
          ["frontier_reasoning", "claude-opus-4-1-20250805"],
          ["long_context", "gemini-2.5-pro"],
        ] as const
      ).map(([profile, model]) => (
        <div key={profile} className={visual.grid}>
          <span className={`mono ${visual.label3 ?? ""}`}>{profile}</span>
          <select style={INPUT} defaultValue={model}>
            <option>{model}</option>
          </select>
        </div>
      ))}
    </div>
  );
};
