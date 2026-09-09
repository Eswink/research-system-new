import { Chip } from "../../components/Chip";
import { UnavailableState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { GAPS, pageSupport } from "../../navigation/pageSupport";
import styles from "../shared/FeaturePage.module.css";

/**
 * 通知中心（T27）：保留通知列表结构；无通知持久化 API——不显示虚构通知/未读数/
 * "已读保存成功"。待审批数量只出现在明确标作待审批的入口。
 */
export function NotificationsPage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "notifications", page: "notifications" });
  return (
    <div className={styles.page} data-testid="gap-page-notifications-notifications">
      <div className={styles.head}>
        <h2 className={styles.heading}>{t("page.notifications.notifications")}</h2>
        <Chip tone="warn">{t("support.gap")}</Chip>
      </div>
      <div className={styles.panel}>
        <div className={styles.panelTitle}>{t("notifications.list")}</div>
        <div style={{ padding: 24, textAlign: "center" }}>
          <span className="empty-mark">{t("notifications.none")}</span>
        </div>
      </div>
      <UnavailableState title={t("notifications.persistence")} reason={support.reason ?? ""} />
      <p className={styles.panelTitle} style={{ marginTop: 8 }}>
        {GAPS.notifications}
      </p>
    </div>
  );
}
