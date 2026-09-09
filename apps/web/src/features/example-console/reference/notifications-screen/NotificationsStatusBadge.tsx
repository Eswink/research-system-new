import { StatusBadge } from "../StatusBadge";

interface NotificationsStatusBadgeProps {
  n:
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
      };
}

export function NotificationsStatusBadge({ n }: NotificationsStatusBadgeProps) {
  return (
    <StatusBadge
      tone={n.severity === "high" ? "danger" : n.severity === "medium" ? "warn" : "neutral"}
      label={n.severity.toUpperCase()}
      icon={n.severity === "high" ? "warn-tri" : n.severity === "medium" ? "diamond" : "circle-o"}
      size="sm"
    />
  );
}
