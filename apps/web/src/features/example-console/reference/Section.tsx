import type * as R from "react";
import visual from "./Section.module.css";

/** Reference: screens/Incidents.jsx; EXAMPLE ONLY. */
export const Section = ({ label, children }: { label: R.ReactNode; children: R.ReactNode }) => (
  <div>
    <div className={visual.caption}>{label}</div>
    {children}
  </div>
);
