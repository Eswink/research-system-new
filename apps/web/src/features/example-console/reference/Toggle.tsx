import visual from "./Toggle.module.css";

/** Reference: screens/OpsScreens.jsx; EXAMPLE ONLY. */
export const Toggle = ({ on, onToggle }: { on: boolean; onToggle: () => void }) => (
  <button
    onClick={onToggle}
    className={visual.action}
    style={{
      background: on ? "var(--accent)" : "var(--bg-sunken)",
      border: `1px solid ${on ? "var(--accent)" : "var(--border-strong)"}`,
    }}
  >
    <div className={visual.overlay} style={{ left: on ? 15 : 1 }} />
  </button>
);
