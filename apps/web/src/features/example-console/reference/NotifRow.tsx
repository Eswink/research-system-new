import visual from "./NotifRow.module.css";

/** Reference: screens/Settings.jsx; EXAMPLE ONLY. */
export const NotifRow = ({
  label,
  desc,
  value,
  onChange,
}: {
  label: string;
  desc: string;
  value: boolean;
  onChange: (value: boolean) => void;
}) => (
  <div className={visual.row}>
    <div className={visual.surface}>
      <div className={visual.label}>{label}</div>
      {desc && <div className={visual.label2}>{desc}</div>}
    </div>
    <button
      onClick={() => {
        onChange(!value);
      }}
      className={visual.action}
      style={{
        background: value ? "var(--accent)" : "var(--bg-sunken)",
        border: `1px solid ${value ? "var(--accent)" : "var(--border-strong)"}`,
      }}
    >
      <div className={visual.overlay} style={{ left: value ? 20 : 2 }} />
    </button>
  </div>
);
