import { FormRow } from "../FormRow";
import { Select } from "../Select";

interface SettingsPfLanguage2Props {
  t: (key: string, fallback?: string) => string;
  lang: string;
  setLang: (next: string) => void;
}

export function SettingsPfLanguage2({ t, lang, setLang }: SettingsPfLanguage2Props) {
  return (
    <FormRow label={t("st.pf.language")}>
      <Select
        value={lang}
        onChange={(v) => {
          setLang(v);
        }}
        options={[
          { value: "en", label: "English" },
          { value: "zh-CN", label: "简体中文" },
        ]}
      />
    </FormRow>
  );
}
