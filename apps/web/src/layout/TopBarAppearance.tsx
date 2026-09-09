import { Icon } from "../components/Icon";
import { useI18n } from "../i18n/useI18n";
import styles from "./TopBar.module.css";
import type { ConsolePreferences } from "./preferences";
import type { TopBarProps } from "./topBarProps";

export function TopBarAppearance({ preferences, onPreferencesChange }: TopBarProps) {
  const { t, language, setLanguage } = useI18n();
  return (
    <>
      <button
        type="button"
        className={styles.langBtn}
        data-testid="toggle-language"
        aria-label="switch language"
        onClick={() => {
          setLanguage(language === "zh" ? "en" : "zh");
        }}
      >
        <span className={language === "en" ? styles.langActive : undefined}>EN</span>
        <span className={language === "zh" ? styles.langActive : undefined}>中</span>
      </button>
      <TopBarAppearanceAction {...{ language, onPreferencesChange, preferences }} />
      <button
        type="button"
        className={styles.iconBtn}
        data-testid="toggle-theme"
        title={t("app.theme")}
        aria-label={t("app.theme")}
        onClick={() => {
          onPreferencesChange({
            ...preferences,
            theme: preferences.theme === "dark" ? "light" : "dark",
          });
        }}
      >
        <Icon name={preferences.theme === "dark" ? "circle" : "circle-o"} size={12} />
      </button>
    </>
  );
}

interface TopBarAppearanceActionProps {
  language: string;
  onPreferencesChange: (next: ConsolePreferences) => void;
  preferences: ConsolePreferences;
}

function TopBarAppearanceAction({
  language,
  onPreferencesChange,
  preferences,
}: TopBarAppearanceActionProps) {
  return (
    <button
      type="button"
      className={styles.iconBtn}
      data-testid="toggle-density"
      title={language === "zh" ? "切换界面密度" : "Toggle density"}
      aria-label="Toggle density"
      onClick={() => {
        onPreferencesChange({
          ...preferences,
          density: preferences.density === "normal" ? "compact" : "normal",
        });
      }}
    >
      <Icon name="menu" size={12} />
    </button>
  );
}
