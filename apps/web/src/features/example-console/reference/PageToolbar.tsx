import type * as R from "react";
import visual from "./PageToolbar.module.css";

/** Reference: components/patterns.jsx; EXAMPLE ONLY. */
export const PageToolbar = ({
  title,
  subtitle,
  children,
  actions,
}: {
  title: R.ReactNode;
  subtitle?: R.ReactNode;
  children?: R.ReactNode;
  actions?: R.ReactNode;
}) => (
  <div className={visual.row}>
    <div>
      {subtitle && <div className={visual.caption}>{subtitle}</div>}
      <div className={visual.label}>{title}</div>
    </div>
    <div className={visual.row2}>{children}</div>
    {actions && <div className={visual.row3}>{actions}</div>}
  </div>
);
