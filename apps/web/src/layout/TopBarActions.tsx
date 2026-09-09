import { Icon } from "../components/Icon";
import { QuickCreate } from "../features/example-console/reference/QuickCreate";
import { useI18n } from "../i18n/useI18n";
import { usePresentation } from "../navigation/usePresentation";
import styles from "./TopBar.module.css";
import type { TopBarProps } from "./topBarProps";

const CREATE_ROUTES: Readonly<Record<string, string>> = {
  project: "#/portfolio/projects",
  experiment: "#/portfolio/experiments",
  prompt: "#/library/prompts",
  notebook: "#/library/notebooks",
  alert: "#/ops/alerts",
  schedule: "#/ops/schedules",
  report: "#/insights/reports",
};

export function TopBarActions(props: TopBarProps) {
  const { t } = useI18n();
  const { source } = usePresentation();
  return (
    <>
      <button
        type="button"
        className={styles.searchBtn}
        onClick={props.onOpenPalette}
        data-testid="open-palette"
        aria-label={t("app.search")}
      >
        <Icon name="search" size={11} />
        <span>{t("app.search")}</span>
        <kbd>⌘K</kbd>
      </button>
      <QuickCreate
        onCreate={(kind) => {
          const route = CREATE_ROUTES[kind];
          if (route) props.onNavigate(route);
        }}
      />
      <span className={styles.separator} />
      <button
        type="button"
        className={styles.iconBtn}
        data-testid="open-command-center"
        onClick={props.onOpenCommandCenter}
        title={t("app.commandCenter")}
        aria-label={t("app.commandCenter")}
      >
        <Icon name="external" size={12} />
      </button>
      <button
        type="button"
        className={styles.iconBtn}
        data-testid="open-notifications"
        onClick={props.onOpenNotifications}
        title={t("notifications.title")}
        aria-label={t("notifications.title")}
      >
        <Icon name="q" size={12} />
        {source === "example" && <span className={styles.exampleUnread} />}
      </button>
    </>
  );
}
