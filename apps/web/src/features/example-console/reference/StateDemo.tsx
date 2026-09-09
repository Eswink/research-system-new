import type * as R from "react";
import visual from "./StateDemo.module.css";

/** Reference: screens/States.jsx; EXAMPLE ONLY. */
export const StateDemo = ({ children }: { children: R.ReactNode }) => (
  <div className={visual.surface}>{children}</div>
);
