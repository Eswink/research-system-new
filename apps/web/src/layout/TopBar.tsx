import { Icon } from "../components/Icon";
import { useI18n } from "../i18n/useI18n";
import { domainOf, type Route } from "../navigation/registry";
import type { ConsolePreferences } from "./preferences";
import styles from "./TopBar.module.css";

function Breadcrumb({ route }: { route: Route }) {
  const { t } = useI18n();
  if (route.domain === route.page) {
    return (
      <div className={styles.crumb}>
        <span className={styles.crumbFaint}>{t("app.name")}</span>
        <Icon name="chevron-r" size={10} />
        <span className={styles.crumbCurrent}>
          {t(`dom.${route.domain}` as Parameters<typeof t>[0])}
        </span>
      </div>
    );
  }
  const domain = domainOf(route.domain as Parameters<typeof domainOf>[0]);
  return (
    <div className={styles.crumb}>
      <span className={styles.crumbFaint}>
        {t(`dom.${domain?.id ?? route.domain}` as Parameters<typeof t>[0])}
      </span>
      <Icon name="chevron-r" size={10} />
      <span className={styles.crumbCurrent}>
        {t(`page.${route.domain}.${route.page}` as Parameters<typeof t>[0])}
      </span>
    </div>
  );
}

function IconButton({
  icon,
  label,
  testId,
  onClick,
  active,
}: {
  icon: Parameters<typeof Icon>[0]["name"];
  label: string;
  testId: string;
  onClick: () => void;
  active?: boolean;
}) {
  return (
    <button
      type="button"
      className={styles.iconBtn}
      data-testid={testId}
      onClick={onClick}
      title={label}
      aria-label={label}
      aria-pressed={active}
    >
      <Icon name={icon} size={12} />
    </button>
  );
}

/** 顶栏：面包屑 + 命令面板入口 + 大屏/通知/语言/主题切换。 */
export interface TopBarProps {
  route: Route;
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
  onOpenPalette: () => void;
  onOpenCommandCenter: () => void;
  onOpenNotifications: () => void;
}

export function TopBar(props: TopBarProps) {
  const { route, preferences, onPreferencesChange } = props;
  const { onOpenPalette, onOpenCommandCenter, onOpenNotifications } = props;
  const { t, language, setLanguage } = useI18n();
  const toggleTheme = (): void => {
    onPreferencesChange({ ...preferences, theme: preferences.theme === "dark" ? "light" : "dark" });
  };
  return (
    <header className={styles.topbar}>
      <Breadcrumb route={route} />
      <div className={styles.right}>
        <button
          type="button"
          className={styles.searchBtn}
          onClick={onOpenPalette}
          data-testid="open-palette"
        >
          <Icon name="search" size={11} />
          <span>{t("app.search")}</span>
          <kbd>⌘K</kbd>
        </button>
        <IconButton
          icon="external"
          label={t("app.commandCenter")}
          testId="open-command-center"
          onClick={onOpenCommandCenter}
        />
        <IconButton
          icon="dot"
          label={t("notifications.title")}
          testId="open-notifications"
          onClick={onOpenNotifications}
        />
        <LangToggle
          language={language}
          onToggle={() => { setLanguage(language === "zh" ? "en" : "zh"); }}
        />
        <IconButton
          icon={preferences.theme === "dark" ? "circle" : "circle-o"}
          label={t("app.theme")}
          testId="toggle-theme"
          onClick={toggleTheme}
        />
      </div>
    </header>
  );
}

function LangToggle({ language, onToggle }: { language: string; onToggle: () => void }) {
  return (
    <button
      type="button"
      className={styles.langBtn}
      onClick={onToggle}
      data-testid="toggle-language"
      aria-label="switch language"
    >
      <span className={language === "en" ? styles.langActive : undefined}>EN</span>
      <span className={language === "zh" ? styles.langActive : undefined}>中</span>
    </button>
  );
}
