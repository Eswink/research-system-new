import type * as R from "react";
import type * as E from "../exampleTypes";
import { Icon } from "./Icon";

/** Reference: components/atoms.jsx; EXAMPLE ONLY. */
export const StatusBadge = ({
  tone = "neutral",
  label,
  icon,
  dashed = false,
  filled = false,
  size = "md",
}: E.BadgeProps) => {
  const styles: R.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: 5,
    padding: size === "sm" ? "0 5px" : "1px 7px",
    height: size === "sm" ? 16 : 18,
    borderRadius: 4,
    fontSize: size === "sm" ? 10 : 11,
    fontFamily: "var(--font-mono)",
    fontWeight: 500,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    whiteSpace: "nowrap",
    border: `1px ${dashed ? "dashed" : "solid"} var(--${
      tone === "neutral" ? "border" : tone
    }-line)`,
    background: filled ? `var(--${tone === "neutral" ? "bg-raised" : tone}-dim)` : "transparent",
    color: tone === "neutral" ? "var(--fg-muted)" : `var(--${tone})`,
  };
  return (
    <span style={styles} role="status">
      {icon && <Icon name={icon} size={10} />}
      <span>{label}</span>
    </span>
  );
};
