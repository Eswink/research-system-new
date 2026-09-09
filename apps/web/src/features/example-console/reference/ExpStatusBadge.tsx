import type * as E from "../exampleTypes";
import visual from "./ExpStatusBadge.module.css";
import { Icon } from "./Icon";
import { StatusBadge } from "./StatusBadge";

/** Reference: screens/Experiments.jsx; EXAMPLE ONLY. */
export const ExpStatusBadge = ({ status }: { status: string }) => {
  const map: Record<string, E.BadgeProps> = {
    QUEUED: { tone: "neutral", icon: "circle-dash", label: "QUEUED", dashed: true },
    RUNNING: { tone: "info", icon: "spin", label: "RUNNING" },
    PAUSED: { tone: "warn", icon: "pause", label: "PAUSED", filled: true },
    SUCCEEDED: { tone: "success", icon: "check", label: "DONE", filled: true },
    FAILED: { tone: "danger", icon: "x", label: "FAILED", filled: true },
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
