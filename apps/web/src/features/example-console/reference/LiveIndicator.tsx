import { Icon } from "./Icon";
import visual from "./LiveIndicator.module.css";

/** Reference: components/atoms.jsx; EXAMPLE ONLY. */
export const LiveIndicator = ({
  state = "live",
  behind = 0,
}: {
  state?: string;
  behind?: number;
}) => {
  const cfg =
    {
      live: { color: "var(--success)", icon: "dot", label: "LIVE", pulse: true },
      reconnecting: { color: "var(--warn)", icon: "spin", label: "RECONNECTING" },
      behind: { color: "var(--warn)", icon: "clock", label: `BEHIND ${String(behind)}` },
      offline: { color: "var(--fg-faint)", icon: "wifi-off", label: "OFFLINE" },
    }[state] ?? {};
  return (
    <span className={visual.row} style={{ color: cfg.color }}>
      <span className={visual.row2}>
        <Icon name={cfg.icon} size={10} />
        {cfg.pulse && <span className={visual.overlay} style={{ background: cfg.color }} />}
      </span>
      <span>{cfg.label}</span>
    </span>
  );
};
