import visual from "./ErrCount.module.css";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const ErrCount = ({ tone, n }: { tone: string; n: number }) => (
  <span
    className={visual.row}
    style={{
      background: `var(--${tone}-dim)`,
      border: `1px solid var(--${tone}-line)`,
      color: `var(--${tone})`,
    }}
  >
    {n}
  </span>
);
