import visual from "../AlertsScreen.module.css";
import { Icon } from "../Icon";
import { StatusBadge } from "../StatusBadge";

interface AlertsSection3Props {
  c: { name: string; type: string; status: string; stats: string };
}

export function AlertsSection3({ c }: AlertsSection3Props) {
  return (
    <div className={visual.row}>
      <Icon
        name={
          c.type === "chat"
            ? "menu"
            : c.type === "pager"
              ? "warn-tri"
              : c.type === "email"
                ? "external"
                : "wifi"
        }
        size={12}
        className={visual.surface8}
      />
      <span className={visual.label3}>{c.name}</span>
      <StatusBadge
        tone={c.status === "healthy" ? "success" : "warn"}
        label={c.status.toUpperCase()}
        icon={c.status === "healthy" ? "check" : "warn-tri"}
        size="sm"
      />
    </div>
  );
}
