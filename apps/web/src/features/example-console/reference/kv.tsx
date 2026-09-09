import type * as R from "react";
import visual from "./kv.module.css";

/** Reference: screens/Timeline.jsx; EXAMPLE ONLY. */
export const KV = ({
  k,
  v,
  unknown,
  warn,
}: {
  k: R.ReactNode;
  v: R.ReactNode;
  unknown?: boolean;
  warn?: boolean;
}) => (
  <div className={visual.grid}>
    <span className={visual.surface}>{k}</span>
    <span
      className="mono"
      style={{ color: unknown ? "var(--unknown)" : warn ? "var(--warn)" : "var(--fg)" }}
      title={typeof v === "string" ? v : ""}
    >
      {v}
    </span>
  </div>
);
