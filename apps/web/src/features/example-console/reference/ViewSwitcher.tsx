import type * as E from "../exampleTypes";
import { Icon } from "./Icon";
import visual from "./ViewSwitcher.module.css";

/** Reference: components/patterns.jsx; EXAMPLE ONLY. */
export const ViewSwitcher = ({
  views,
  value,
  onChange,
}: {
  views: E.Option[];
  value: string;
  onChange: (value: string) => void;
}) => (
  <div className={visual.row}>
    {views.map((v) => {
      const active = v.value === value;
      return (
        <button
          type="button"
          key={v.value}
          aria-pressed={active}
          disabled={v.disabled}
          onClick={() => {
            onChange(v.value);
          }}
          className={visual.row2}
          style={{
            background: active ? "var(--bg-panel)" : "transparent",
            color: active ? "var(--fg)" : "var(--fg-muted)",
            fontWeight: active ? 500 : 400,
            boxShadow: active ? "var(--shadow-1)" : "none",
          }}
        >
          {v.icon && <Icon name={v.icon} size={10} />}
          {v.label}
        </button>
      );
    })}
  </div>
);
