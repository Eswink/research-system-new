import type * as R from "react";
import visual from "./DrawerSection.module.css";

/** Reference: screens/Timeline.jsx; EXAMPLE ONLY. */
export const DrawerSection = ({
  title,
  children,
}: {
  title: R.ReactNode;
  children: R.ReactNode;
}) => (
  <div className={visual.surface}>
    <div className={visual.caption}>{title}</div>
    <div className={visual.column}>{children}</div>
  </div>
);
