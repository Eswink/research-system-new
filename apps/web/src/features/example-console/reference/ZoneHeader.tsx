import type * as R from "react";
import { Icon } from "./Icon";
import visual from "./ZoneHeader.module.css";

/** Reference: screens/DryRun.jsx; EXAMPLE ONLY. */
export const ZoneHeader = ({
  icon,
  title,
  count,
  extra,
}: {
  icon: string;
  title: R.ReactNode;
  count?: number;
  extra?: R.ReactNode;
}) => (
  <div className={visual.row}>
    <Icon name={icon} size={12} className={visual.surface} />
    <span className={visual.label}>{title}</span>
    {typeof count === "number" && <span className="chip">{count}</span>}
    <span className={visual.row2}>{extra}</span>
  </div>
);
