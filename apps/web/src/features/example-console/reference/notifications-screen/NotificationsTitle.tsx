import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import { PageToolbar } from "../PageToolbar";
import { ViewSwitcher } from "../ViewSwitcher";

interface NotificationsTitleProps {
  t: (key: string, fallback?: string) => string;
  filter: string;
  setFilter: Dispatch<SetStateAction<string>>;
  all: (
    | {
        id: string;
        kind: string;
        severity: string;
        subject: string;
        at: string;
        read: boolean;
        ref: string;
      }
    | {
        id: string;
        kind: string;
        severity: string;
        subject: string;
        at: string;
        read: boolean;
        ref?: never;
      }
  )[];
  unreadCount: number;
  markAll: () => void;
}

export function NotificationsTitle({
  t,
  filter,
  setFilter,
  all,
  unreadCount,
  markAll,
}: NotificationsTitleProps) {
  return (
    <PageToolbar title={t("nc.title")} subtitle={t("nc.subtitle")}>
      <ViewSwitcher
        value={filter}
        onChange={setFilter}
        views={[
          { value: "all", label: `${t("nc.all")} (${String(all.length)})` },
          { value: "unread", label: `${t("nc.unread")} (${String(unreadCount)})` },
          { value: "alert", label: t("nc.alerts") },
          { value: "approval", label: t("nc.approvals") },
          { value: "claim", label: t("nc.claims") },
          { value: "run", label: t("nc.runs") },
        ]}
      />
      <button className="btn sm ghost" onClick={markAll}>
        <Icon name="check" size={11} /> {t("nc.markAllRead")}
      </button>
      <button className="btn sm">
        <Icon name="external" size={11} /> {t("nc.settings")}
      </button>
    </PageToolbar>
  );
}
