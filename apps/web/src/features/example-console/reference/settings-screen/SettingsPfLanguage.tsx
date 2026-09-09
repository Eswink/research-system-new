import { FormRow } from "../FormRow";
import { Select } from "../Select";
import visual from "../SettingsScreen.module.css";
import { SettingsPfLanguage2 } from "./SettingsPfLanguage2";

interface SettingsPfLanguageProps {
  t: (key: string, fallback?: string) => string;
  lang: string;
  setLang: (next: string) => void;
}

export function SettingsPfLanguage({ t, lang, setLang }: SettingsPfLanguageProps) {
  return (
    <div className={visual.column5}>
      <SettingsPfLanguage2 {...{ t, lang, setLang }} />
      <FormRow label={t("st.pf.dateFormat")}>
        <Select
          defaultValue="iso"
          options={[
            { value: "iso", label: "2026-08-30 14:33 (ISO 8601)" },
            { value: "us", label: "Aug 30, 2026 2:33 PM" },
            { value: "eu", label: "30/08/2026 14:33" },
          ]}
        />
      </FormRow>
      <FormRow label={t("st.pf.currency")}>
        <Select
          defaultValue="usd"
          options={[
            { value: "usd", label: "Example $ (native)" },
            { value: "jpy", label: "Example ¥ (converted)" },
            { value: "eur", label: "Example € (converted)" },
          ]}
        />
      </FormRow>
      <FormRow label={t("st.pf.digest")} hint={t("st.pf.digestHint")}>
        <Select
          defaultValue="daily"
          options={[
            { value: "off", label: t("st.pf.digestOff") },
            { value: "daily", label: t("st.pf.digestDaily") },
            { value: "weekly", label: t("st.pf.digestWeekly") },
          ]}
        />
      </FormRow>
    </div>
  );
}
