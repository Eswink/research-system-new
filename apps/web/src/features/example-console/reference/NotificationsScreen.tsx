import { useMemo, useState, type Dispatch, type SetStateAction } from "react";
import FIX_NOTIFICATIONS from "../data/notifications.json";
import type * as FixtureTypes from "../fixtureTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { EmptyState } from "./EmptyState";
import { Icon } from "./Icon";
import visual from "./NotificationsScreen.module.css";
import { NotificationsStatusBadge } from "./notifications-screen/NotificationsStatusBadge";
import { NotificationsTitle } from "./notifications-screen/NotificationsTitle";

type NotificationItem =
  FixtureTypes.Notification | (Omit<FixtureTypes.Notification, "ref"> & { ref?: never });

const EXTRA_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "ntf_06",
    kind: "run",
    severity: "low",
    subject: "Run rag · adversarial · v7 succeeded task_ret_bm25",
    at: "2026-08-27T13:20:12Z",
    read: true,
  },
  {
    id: "ntf_07",
    kind: "alert",
    severity: "medium",
    subject: "Endpoint prod-us-east latency p95 breached 1.2s SLO",
    at: "2026-08-27T12:12:00Z",
    read: false,
    ref: "alrt_i_02",
  },
  {
    id: "ntf_08",
    kind: "approval",
    severity: "low",
    subject: "Approval processed · increase_budget +$500 auto-granted",
    at: "2026-08-27T10:03:00Z",
    read: true,
  },
  {
    id: "ntf_09",
    kind: "claim",
    severity: "high",
    subject: "Claim clm_h4_zh_delta refuted after re-run — see evidence",
    at: "2026-08-26T22:14:00Z",
    read: false,
    ref: "clm_h4_zh_delta",
  },
  {
    id: "ntf_10",
    kind: "report",
    severity: "low",
    subject: "Report weekly-med-qa compiled and posted to Slack",
    at: "2026-08-26T09:00:00Z",
    read: true,
  },
  {
    id: "ntf_11",
    kind: "system",
    severity: "low",
    subject: "System · SSO certificate rotated (auto)",
    at: "2026-08-26T05:00:00Z",
    read: true,
  },
  {
    id: "ntf_12",
    kind: "run",
    severity: "medium",
    subject: "Run steering · final degraded to SUPERVISED autonomy",
    at: "2026-08-25T18:04:00Z",
    read: true,
  },
];

const KIND_ICONS: Record<string, string> = {
  alert: "warn-tri",
  approval: "shield",
  claim: "diamond",
  run: "play",
  report: "book",
  system: "menu",
};

const SEVERITY_COLORS: Record<string, string> = {
  high: "var(--danger)",
  medium: "var(--warn)",
  low: "var(--fg-muted)",
};

function groupNotifications(items: NotificationItem[]): Record<string, NotificationItem[]> {
  const groups: Record<string, NotificationItem[]> = {};
  items.forEach((item) => {
    const day = item.at.slice(0, 10);
    (groups[day] ??= []).push(item);
  });
  return groups;
}

export const NotificationsScreen = () => {
  const { t } = useI18n();
  const [filter, setFilter] = useState("all");
  const [readMap, setReadMap] = useState(() =>
    Object.fromEntries(FIX_NOTIFICATIONS.map((n) => [n.id, n.read])),
  );

  const all = useMemo(() => [...FIX_NOTIFICATIONS, ...EXTRA_NOTIFICATIONS], []);

  const filtered = all.filter((n) =>
    filter === "all" ? true : filter === "unread" ? !(readMap[n.id] ?? n.read) : n.kind === filter,
  );

  const markAll = () => {
    setReadMap(Object.fromEntries(all.map((n) => [n.id, true])));
  };
  const toggleRead = (id: string) => {
    setReadMap((prev) => ({
      ...prev,
      [id]: !(prev[id] ?? all.find((n) => n.id === id)?.read ?? false),
    }));
  };

  const groups = groupNotifications(filtered);
  const dayKeys = Object.keys(groups).sort((a, b) => b.localeCompare(a));

  const unreadCount = all.filter((n) => !(readMap[n.id] ?? n.read)).length;

  return (
    <NotificationsLayout
      {...{
        t,
        filter,
        setFilter,
        all,
        unreadCount,
        markAll,
        filtered,
        groups,
        dayKeys,
        readMap,
        toggleRead,
      }}
    />
  );
};

function NotificationsLayout({
  t,
  filter,
  setFilter,
  all,
  unreadCount,
  markAll,
  filtered,
  groups,
  dayKeys,
  readMap,
  toggleRead,
}: {
  t: (key: string, fallback?: string) => string;
  filter: string;
  setFilter: Dispatch<SetStateAction<string>>;
  all: NotificationItem[];
  unreadCount: number;
  markAll: () => void;
  filtered: NotificationItem[];
  groups: Record<string, NotificationItem[]>;
  dayKeys: string[];
  readMap: Record<string, boolean>;
  toggleRead: (id: string) => void;
}) {
  return (
    <div className={visual.column}>
      <NotificationsTitle {...{ t, filter, setFilter, all, unreadCount, markAll }} />

      {filtered.length === 0 ? (
        <EmptyState icon="check" title={t("nc.emptyTitle")} description={t("nc.emptyDesc")} />
      ) : (
        <NotificationGroups {...{ t, groups, dayKeys, readMap, toggleRead }} />
      )}
    </div>
  );
}

function NotificationGroups({
  t,
  groups,
  dayKeys,
  readMap,
  toggleRead,
}: Pick<
  Parameters<typeof NotificationsLayout>[0],
  "t" | "groups" | "dayKeys" | "readMap" | "toggleRead"
>) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      {dayKeys.map((day) => (
        <div key={day}>
          <div className={visual.caption}>
            {day} · {(groups[day] ?? []).length} {t("nc.events")}
          </div>
          {(groups[day] ?? []).map((notification) => (
            <NotificationRow
              key={notification.id}
              notification={notification}
              unread={!(readMap[notification.id] ?? notification.read)}
              onToggle={toggleRead}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

function NotificationRow({
  notification,
  unread,
  onToggle,
}: {
  notification: NotificationItem;
  unread: boolean;
  onToggle: (id: string) => void;
}) {
  return (
    <div
      onClick={() => {
        onToggle(notification.id);
      }}
      className={visual.grid}
      style={{ background: unread ? "var(--accent-dim)" : "transparent" }}
    >
      <span
        className={visual.surface}
        style={{ background: unread ? "var(--accent)" : "transparent" }}
      />
      <Icon
        name={KIND_ICONS[notification.kind] ?? "circle-o"}
        size={13}
        style={{ color: SEVERITY_COLORS[notification.severity] }}
      />
      <span className={`chip ${visual.caption2 ?? ""}`}>{notification.kind.toUpperCase()}</span>
      <NotificationsStatusBadge n={notification} />
      <span className={visual.label} style={{ fontWeight: unread ? 500 : 400 }}>
        {notification.subject}
      </span>
      <span className={`mono ${visual.caption3 ?? ""}`}>
        {new Date(notification.at).toISOString().slice(11, 16)} UTC
      </span>
      <Icon name="chevron-r" size={10} className={visual.surface2} />
    </div>
  );
}
