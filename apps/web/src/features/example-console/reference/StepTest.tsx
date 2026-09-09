import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import visual from "./StepTest.module.css";

/** Reference: screens/Setup.jsx; EXAMPLE ONLY. */
export const StepTest = () => {
  const { t } = useI18n();
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.label}>{t("st.test.title")}</div>
      <div className={visual.label2}>
        <div>
          <span className={visual.surface}>POST</span>{" "}
          <span className={visual.surface2}>/llm-endpoints/ep_anthropic_direct/test</span>
        </div>
        <div className={visual.surface3}>
          <span className={visual.surface4}>ok</span> ·{" "}
          <span className={visual.surface5}>true</span>
        </div>
        <div>
          <span className={visual.surface6}>returned_model_name</span> · claude-sonnet-4-20250514
        </div>
        <div>
          <span className={visual.surface7}>system_fingerprint</span> ·{" "}
          <span className={visual.surface8}>{t("st.test.notProvided")}</span>{" "}
          <span className={visual.caption}>({"provider_fingerprint_available"}: false)</span>
        </div>
        <div>
          <span className={visual.surface9}>latency_ms</span> · 302
        </div>
      </div>
      <div className={visual.row}>
        <Icon name="q" size={12} className={visual.surface10} />
        <span>
          <strong>{t("st.test.reprodTitle")}</strong> {t("st.test.reprodMsg")}{" "}
          <span className="mono">system_fingerprint</span>
          {t("st.test.reprodMsg2")}
        </span>
      </div>
    </div>
  );
};
