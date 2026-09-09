import visual from "./GateChip.module.css";
import { Icon } from "./Icon";

/** Reference: components/atoms.jsx; EXAMPLE ONLY. */
export const GateChip = ({ type }: { type: string }) => {
  const map: Record<string, { color: string; label: string }> = {
    POLICY_GATE: { color: "var(--accent)", label: "POLICY" },
    BUDGET_GATE: { color: "var(--warn)", label: "BUDGET" },
    QUALITY_GATE: { color: "var(--success)", label: "QUALITY" },
    HUMAN_GATE: { color: "var(--fg-muted)", label: "HUMAN" },
    SECURITY_GATE: { color: "var(--danger)", label: "SECURITY" },
    PUBLISH_GATE: { color: "var(--unknown)", label: "PUBLISH" },
  };
  const cfg = map[type] ?? { color: "var(--unknown)", label: type };
  return (
    <span className={visual.row} style={{ border: `1px solid ${cfg.color}44`, color: cfg.color }}>
      <Icon name="shield" size={9} /> {cfg.label}
    </span>
  );
};
