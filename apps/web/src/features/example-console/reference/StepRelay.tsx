import { useExampleI18n as useI18n } from "../useExampleI18n";
import { FormField } from "./FormField";
import { Icon } from "./Icon";
import { INPUT } from "./setupInput";
import visual from "./StepRelay.module.css";

/** Reference: screens/Setup.jsx; EXAMPLE ONLY. */
export const StepRelay = () => {
  const { t } = useI18n();
  return <StepRelayFName {...{ t }} />;
};

interface StepRelayFNameProps {
  t: (key: string, fallback?: string) => string;
}

function StepRelayFName({ t }: StepRelayFNameProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.label}>{t("st.addEndpoint")}</div>
      <div className={visual.label2}>{t("st.addDesc")}</div>

      <FormField label={t("st.f.name")}>
        <input className="input" defaultValue="Anthropic Direct" style={INPUT} />
      </FormField>
      <FormField label={t("st.f.baseUrl")}>
        <input
          className="input"
          defaultValue="https://api.anthropic.com"
          style={{ ...INPUT, fontFamily: "var(--font-mono)" }}
        />
      </FormField>
      <div className={visual.grid}>
        <FormField label={t("st.f.protocol")}>
          <select style={INPUT}>
            <option>OPENAI_COMPATIBLE</option>
          </select>
        </FormField>
        <FormField label={t("st.f.apiStyle")}>
          <select style={INPUT}>
            <option>chat_completions</option>
            <option>responses</option>
          </select>
        </FormField>
      </div>
      <StepRelayFormField {...{ t }} />
      <div className={visual.grid2}>
        <FormField label={t("st.f.timeout")}>
          <input style={INPUT} defaultValue="60" />
        </FormField>
        <FormField label={t("st.f.retries")}>
          <input style={INPUT} defaultValue="3" />
        </FormField>
        <FormField label={t("st.f.concurrency")}>
          <input style={INPUT} defaultValue="16" />
        </FormField>
      </div>
    </div>
  );
}

interface StepRelayFormFieldProps {
  t: (key: string, fallback?: string) => string;
}

function StepRelayFormField({ t }: StepRelayFormFieldProps) {
  return (
    <FormField
      label={
        <>
          {t("st.f.apiKey")} <span className={visual.surface}>· {t("st.f.apiKeyHint")}</span>
        </>
      }
    >
      <div className={visual.surface2}>
        <input
          type="password"
          defaultValue="sk-ant-••••••••••••••••••••••••••••••••••••"
          style={{ ...INPUT, paddingLeft: 32, fontFamily: "var(--font-mono)" }}
        />
        <Icon name="lock" size={12} className={visual.overlay} />
      </div>
    </FormField>
  );
}
