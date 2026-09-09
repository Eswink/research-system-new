import type * as E from "../exampleTypes";
import { Icon } from "./Icon";
import visual from "./ProjectStatusBadge.module.css";
import { StatusBadge } from "./StatusBadge";

/** Reference: screens/Projects.jsx; EXAMPLE ONLY. */
export const ProjectStatusBadge = ({ status }: { status: string }) => {
  const map: Record<string, E.BadgeProps> = {
    RUNNING: { tone: "info", icon: "spin", label: "RUNNING" },
    PAUSED: { tone: "warn", icon: "pause", label: "PAUSED", filled: true },
    DRAFT: { tone: "neutral", icon: "circle-o", label: "DRAFT", dashed: true },
    SUCCEEDED: { tone: "success", icon: "check", label: "DONE", filled: true },
    FAILED: { tone: "danger", icon: "x", label: "FAILED", filled: true },
    ARCHIVED: { tone: "neutral", icon: "lock", label: "ARCHIVED" },
  };
  const cfg = map[status] ?? { tone: "unknown", label: status };
  if (cfg.tone === "info")
    return (
      <span className={visual.row}>
        <Icon name={cfg.icon} size={10} /> {cfg.label}
      </span>
    );
  return <StatusBadge {...cfg} />;
};
