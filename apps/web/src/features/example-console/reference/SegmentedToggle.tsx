import type * as E from "../exampleTypes";
import { PECustomIcon } from "./PECustomIcon";
import visual from "./SegmentedToggle.module.css";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const SegmentedToggle = ({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (value: string) => void;
  options: E.Option[];
}) => (
  <div className={visual.row}>
    {options.map((opt) => {
      const active = opt.value === value;
      return (
        <button
          key={opt.value}
          onClick={() => {
            onChange(opt.value);
          }}
          className={`btn sm ghost ${visual.action ?? ""}`}
          style={{
            background: active ? "var(--bg-panel)" : "transparent",
            border: active ? "1px solid var(--border-strong)" : "1px solid transparent",
            color: active ? "var(--fg)" : "var(--fg-muted)",
            fontWeight: active ? 500 : 400,
            boxShadow: active ? "var(--shadow-1)" : "none",
          }}
        >
          <PECustomIcon name={opt.icon} /> {opt.label}
        </button>
      );
    })}
  </div>
);
