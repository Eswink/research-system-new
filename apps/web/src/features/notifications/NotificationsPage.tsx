import { api } from "../../api/client";
import type { NotificationDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";

/**
 * 通知中心（WP-G）：GET /notifications 的 outbox 事件投影（白名单类型，
 * 不含 payload 内容）。无实时推送端点——列表数量只来自当前投影。
 */
export function NotificationsPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  const view = useResource("notifications", () => api.notifications());
  return (
    <section className={styles.page} data-testid="notifications-page">
      <PageHeader
        title={zh ? "通知" : "Notifications"}
        kicker="NOTIFICATIONS"
        description={
          zh
            ? "来自持久化事件流的投影（真相是事件，不是第二套通知存储）。"
            : [
                "A projection of the persisted event stream; events are the truth, ",
                "not a second store.",
              ].join("")
        }
        actions={
          <button
            type="button"
            className="btn"
            disabled={view.phase === "loading"}
            onClick={view.reload}
          >
            {zh ? "刷新" : "Refresh"}
          </button>
        }
      />
      <ResourceBoundary state={view}>
        {view.data !== null && (
          <NotificationsBody data={view.data.notifications} zh={zh} onChanged={view.reload} />
        )}
      </ResourceBoundary>
      {view.data !== null && <p className={styles.notice}>{view.data.note}</p>}
    </section>
  );
}

function NotificationsBody({
  data,
  zh,
  onChanged,
}: {
  data: NotificationDto[];
  zh: boolean;
  onChanged: () => void;
}) {
  if (data.length === 0) {
    return <EmptyState message={zh ? "没有可显示的通知事件" : "No notification events"} />;
  }
  return (
    <ul className={styles.list} data-testid="notifications-list">
      {data.map((item) => (
        <NotificationRow key={item.id} item={item} zh={zh} onRead={onChanged} />
      ))}
    </ul>
  );
}

function NotificationRow({
  item,
  zh,
  onRead,
}: {
  item: NotificationDto;
  zh: boolean;
  onRead: () => void;
}) {
  const href =
    item.run_id === null ? null : `#/run/timeline?run=${encodeURIComponent(item.run_id)}`;
  return (
    <li className={styles.notice}>
      <Chip tone={item.read ? "neutral" : "accent"}>
        {item.read ? (zh ? "已读" : "read") : zh ? "未读" : "unread"}
      </Chip>{" "}
      <span className="mono">{item.type}</span>
      {href !== null && (
        <>
          {" "}
          · run <a href={href}>{item.run_id}</a>
        </>
      )}{" "}
      · {item.occurred_at}
      {item.read ? null : (
        <button
          type="button"
          className="btn sm ghost"
          onClick={() => {
            void api.markNotificationRead(item.id).then(onRead);
          }}
        >
          {zh ? "标为已读" : "Mark read"}
        </button>
      )}
    </li>
  );
}
