import type * as E from "../exampleTypes";
import { Icon } from "./Icon";
import visual from "./RunStateBadge.module.css";
import { StatusBadge } from "./StatusBadge";

/** Reference: components/atoms.jsx; EXAMPLE ONLY. */
export const RunStateBadge = ({ state }: { state: string }) => {
  const map: Record<string, E.BadgeProps> = {
    PENDING: { tone: "neutral", icon: "circle-o", label: "PENDING" },
    RUNNING: { tone: "info", icon: "spin", label: "RUNNING", filled: true },
    PAUSED: { tone: "warn", icon: "pause", label: "PAUSED", filled: true },
    SUCCEEDED: { tone: "success", icon: "check", label: "SUCCEEDED", filled: true },
    FAILED: { tone: "danger", icon: "x", label: "FAILED", filled: true },
    CANCELED: { tone: "neutral", icon: "ban", label: "CANCELED" },
  };
  const cfg = map[state] ?? { tone: "unknown", label: state };
  // info tone → use accent
  if (cfg.tone === "info") {
    return (
      <span className={visual.row}>
        <Icon name={cfg.icon} size={10} /> {cfg.label}
      </span>
    );
  }
  return (
    <StatusBadge
      tone={cfg.tone}
      icon={cfg.icon}
      label={cfg.label}
      filled={cfg.filled}
      dashed={cfg.dashed}
    />
  );
};
