import { Icon } from "../components/Icon";
import { useI18n } from "../i18n/useI18n";
import { usePresentation } from "../navigation/usePresentation";
import styles from "./Sidebar.module.css";

export function SidebarIdentity({ collapsed, onOpen }: { collapsed: boolean; onOpen: () => void }) {
  const { source } = usePresentation();
  const { t, language } = useI18n();
  const example = source === "example";
  return (
    <button
      type="button"
      className={styles.user}
      data-testid="nav-open-settings"
      onClick={onOpen}
      title={t("settings.title")}
      aria-label={t("settings.title")}
    >
      <span className={styles.avatar}>{example ? "LT" : "R"}</span>
      {!collapsed && (
        <span className={styles.userText}>
          <span className={styles.userName}>
            {example ? (language === "zh" ? "田中 玲央" : "Leo Tanaka") : t("app.user")}
          </span>
          <span className={styles.userMeta}>
            {example
              ? "l.tanaka@research.io · EXAMPLE"
              : language === "zh"
                ? "个人工作区"
                : "Personal workspace"}
          </span>
        </span>
      )}
      {!collapsed && <Icon name="chevron-r" size={10} />}
    </button>
  );
}
