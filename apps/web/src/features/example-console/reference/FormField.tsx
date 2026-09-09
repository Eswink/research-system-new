import type * as R from "react";
import visual from "./FormField.module.css";

/** Reference: screens/Setup.jsx; EXAMPLE ONLY. */
export const FormField = ({ label, children }: { label: R.ReactNode; children: R.ReactNode }) => (
  <div className={visual.surface}>
    <div className={visual.label}>{label}</div>
    {children}
  </div>
);
