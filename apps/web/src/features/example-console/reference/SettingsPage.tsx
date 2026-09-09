import type * as R from "react";
import visual from "./SettingsPage.module.css";

/** Reference: screens/Settings.jsx; EXAMPLE ONLY. */
export const SettingsPage = ({
  title,
  subtitle,
  action,
  children,
}: {
  title: R.ReactNode;
  subtitle?: R.ReactNode;
  action?: R.ReactNode;
  children: R.ReactNode;
}) => (
  <div className={visual.surface}>
    <div className={visual.row}>
      <div className={visual.surface2}>
        <div className={visual.label}>{title}</div>
        {subtitle && <div className={visual.label2}>{subtitle}</div>}
      </div>
      {action}
    </div>
    {children}
  </div>
);
