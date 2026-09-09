import type * as E from "../exampleTypes";
import visual from "./SegmentedField.module.css";

/** Reference: screens/ProtocolEditor.sections.jsx; EXAMPLE ONLY. */
export const SegmentedField = ({
  value,
  onChange,
  options,
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  options: E.Option[];
  disabled?: boolean;
}) => (
  <div
    className={visual.row}
    style={{ opacity: disabled ? 0.55 : 1, pointerEvents: disabled ? "none" : "auto" }}
  >
    {options.map((opt) => {
      const active = opt.value === value;
      return (
        <button
          key={opt.value}
          onClick={() => {
            onChange(opt.value);
          }}
          className={visual.action}
          style={{
            background: active ? "var(--bg-panel)" : "transparent",
            border: active ? "1px solid var(--border-strong)" : "1px solid transparent",
            color: active ? "var(--fg)" : "var(--fg-muted)",
            fontWeight: active ? 500 : 400,
          }}
        >
          {opt.label}
        </button>
      );
    })}
  </div>
);
