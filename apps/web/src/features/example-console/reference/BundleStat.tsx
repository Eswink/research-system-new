import type * as R from "react";
import visual from "./BundleStat.module.css";

/** Reference: screens/Govern.jsx; EXAMPLE ONLY. */
export const BundleStat = ({
  label,
  value,
  sub,
  unknown,
}: {
  label: R.ReactNode;
  value: R.ReactNode;
  sub?: R.ReactNode;
  unknown?: boolean;
}) => (
  <div
    className={visual.surface}
    style={{
      background: unknown ? "var(--unknown-dim)" : "var(--bg-raised)",
      border: `1px ${unknown ? "dashed" : "solid"} ${
        unknown ? "var(--unknown-line)" : "var(--border)"
      }`,
    }}
  >
    <div className={visual.caption}>{label}</div>
    <div className={visual.label}>{value}</div>
    <div className={visual.label2}>{sub}</div>
  </div>
);
