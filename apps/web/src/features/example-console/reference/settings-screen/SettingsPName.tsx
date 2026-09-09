import { FormRow } from "../FormRow";
import { Select } from "../Select";
import visual from "../SettingsScreen.module.css";
import { TextInput } from "../TextInput";

interface SettingsPNameProps {
  t: (key: string, fallback?: string) => string;
  lang: string;
}

export function SettingsPName({ t, lang }: SettingsPNameProps) {
  return (
    <div className={visual.row2}>
      <div className={visual.row3}>LT</div>
      <div className={visual.column}>
        <FormRow label={t("st.p.name")}>
          <TextInput defaultValue={lang === "zh-CN" ? "田中 玲央" : "Leo Tanaka"} />
        </FormRow>
        <FormRow label={t("st.p.email")}>
          <TextInput mono defaultValue="leo.tanaka@research.io" />
        </FormRow>
        <FormRow label={t("st.p.role")}>
          <Select
            defaultValue="pi"
            options={[
              { value: "pi", label: t("st.p.rolePI") },
              { value: "researcher", label: t("st.p.roleR") },
              { value: "reviewer", label: t("st.p.roleRev") },
              { value: "admin", label: t("st.p.roleAdmin") },
            ]}
          />
        </FormRow>
        <FormRow label={t("st.p.timezone")}>
          <Select
            defaultValue="asia_tokyo"
            options={[
              { value: "asia_tokyo", label: "Asia/Tokyo (JST +09:00)" },
              { value: "america_ny", label: "America/New_York (EDT -04:00)" },
              { value: "europe_lon", label: "Europe/London (BST +01:00)" },
            ]}
          />
        </FormRow>
      </div>
    </div>
  );
}
