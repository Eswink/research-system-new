import { useState } from "react";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import visual from "./NotificationBell.module.css";

/** Reference: components/patterns.jsx; EXAMPLE ONLY. */
export const NotificationBell = ({
  items = [],
  onOpenAll,
}: {
  items?: E.Notification[];
  onOpenAll: () => void;
}) => {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const unread = items.filter((n) => !n.read).length;
  return (
    <div className={visual.surface}>
      <button
        className="btn sm ghost"
        onClick={() => {
          setOpen(!open);
        }}
        title="Notifications"
      >
        <Icon name="q" size={11} />
        {unread > 0 && <span className={visual.overlay} />}
      </button>
      {open && (
        <>
          <div
            className={visual.overlay2}
            onClick={() => {
              setOpen(false);
            }}
          />
          <NotificationBellSection {...{ t, unread, items, onOpenAll }} />
        </>
      )}
    </div>
  );
};

interface NotificationBellSectionProps {
  t: (key: string, fallback?: string) => string;
  unread: number;
  items: {
    id: string;
    kind: string;
    severity: string;
    subject: string;
    at: string;
    read: boolean;
    ref: string;
  }[];
  onOpenAll: () => void;
}

function NotificationBellSection({ t, unread, items, onOpenAll }: NotificationBellSectionProps) {
  return (
    <div className={visual.overlay3}>
      <div className={visual.row}>
        <span className={visual.label}>{t("nt.title", "Notifications")}</span>
        <span className="chip">
          {unread} {t("nt.unread", "unread")}
        </span>
      </div>
      <NotificationBellSection2 {...{ items }} />
      <div className={visual.label3}>
        <a
          onClick={() => {
            onOpenAll();
          }}
          className={visual.surface5}
        >
          {t("nt.openAll", "View all notifications →")}
        </a>
      </div>
    </div>
  );
}

interface NotificationBellSection2Props {
  items: {
    id: string;
    kind: string;
    severity: string;
    subject: string;
    at: string;
    read: boolean;
    ref: string;
  }[];
}

function NotificationBellSection2({ items }: NotificationBellSection2Props) {
  return (
    <div className={visual.surface2}>
      {items.map((n) => (
        <div
          key={n.id}
          className={visual.row2}
          style={{ background: n.read ? "transparent" : "var(--bg-raised)" }}
        >
          <div
            className={visual.surface3}
            style={{
              background:
                n.severity === "high"
                  ? "var(--danger)"
                  : n.severity === "medium"
                    ? "var(--warn)"
                    : "var(--fg-faint)",
            }}
          />
          <div className={visual.surface4}>
            <div className={visual.label2}>{n.subject}</div>
            <div className={visual.caption}>
              {n.kind} ·{" "}
              {new Date(n.at).toLocaleTimeString("en-GB", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
