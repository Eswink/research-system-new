import { Field } from "../../components/Field";
import { PanelSection } from "../../components/PanelSection";
import { SegmentedToggle } from "../../components/SegmentedToggle";
import { useI18n } from "../../i18n/useI18n";
import type { ConsolePreferences } from "../../layout/preferences";
import styles from "../shared/LivePage.module.css";

export function PreferencesSection({
  preferences,
  onChange,
}: {
  preferences: ConsolePreferences;
  onChange: (next: ConsolePreferences) => void;
}) {
  const { language, t } = useI18n();
  return (
    <PanelSection title={t("settings.preferences")}>
      <div className={styles.page}>
        <PreferenceAppearance preferences={preferences} onChange={onChange} />
        <Field label={language === "zh" ? "界面语言" : "Interface language"}>
          <SegmentedToggle
            ariaLabel={language === "zh" ? "界面语言" : "Interface language"}
            value={preferences.language}
            options={[
              { value: "zh", label: "简体中文" },
              { value: "en", label: "English" },
            ]}
            onChange={(value) => {
              onChange({ ...preferences, language: value === "en" ? "en" : "zh" });
            }}
          />
        </Field>
        <p className={styles.notice}>
          {language === "zh"
            ? "主题、密度和语言是此浏览器的本地偏好，不修改项目、账户或后端策略。"
            : [
                "Theme, density and language are local browser preferences, not project, ",
                "account or backend-policy changes.",
              ].join("")}
        </p>
      </div>
    </PanelSection>
  );
}

function PreferenceAppearance({
  preferences,
  onChange,
}: {
  preferences: ConsolePreferences;
  onChange: (next: ConsolePreferences) => void;
}) {
  const { t } = useI18n();
  return (
    <>
      <Field label={t("app.theme")}>
        <SegmentedToggle
          ariaLabel={t("app.theme")}
          value={preferences.theme}
          options={[
            { value: "dark", label: t("app.theme.dark") },
            { value: "light", label: t("app.theme.light") },
          ]}
          onChange={(value) => {
            onChange({ ...preferences, theme: value === "light" ? "light" : "dark" });
          }}
        />
      </Field>
      <Field label={t("app.density")}>
        <SegmentedToggle
          ariaLabel={t("app.density")}
          value={preferences.density}
          options={[
            { value: "normal", label: t("app.density.normal") },
            { value: "compact", label: t("app.density.compact") },
          ]}
          onChange={(value) => {
            onChange({ ...preferences, density: value === "compact" ? "compact" : "normal" });
          }}
        />
      </Field>
    </>
  );
}
