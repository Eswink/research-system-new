import type * as R from "react";
import visual from "./StatBlock.module.css";

/** Reference: Command Center.html; every metric is a fixed example. */
export const StatBlock = ({
  label,
  value,
  sub,
  color = "var(--fg)",
}: {
  label: string;
  value: R.ReactNode;
  sub?: string;
  color?: string;
}) => (
  <div>
    <div className={visual.caption}>{label}</div>
    <div className={visual.row}>
      <span className={visual.label} style={{ color }}>
        {value}
      </span>
      <span className={visual.label2}>{sub}</span>
    </div>
  </div>
);
