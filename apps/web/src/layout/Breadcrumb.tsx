import { Icon } from "../components/Icon";
import { useI18n } from "../i18n/useI18n";
import type { Route } from "../navigation/registry";
import styles from "./TopBar.module.css";

export function Breadcrumb({ route }: { route: Route }) {
  const { t } = useI18n();
  const domain = route.domain === route.page ? "app.name" : `dom.${route.domain}`;
  const page =
    route.domain === route.page ? `${route.domain}.title` : `page.${route.domain}.${route.page}`;
  return (
    <div className={styles.crumb} aria-label="Breadcrumb">
      <span className={styles.crumbFaint}>{t(domain as Parameters<typeof t>[0])}</span>
      <Icon name="chevron-r" size={10} />
      <span className={styles.crumbCurrent}>{t(page as Parameters<typeof t>[0])}</span>
    </div>
  );
}
