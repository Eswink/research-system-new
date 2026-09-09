import type * as R from "react";
import visual from "./SectionHeader.module.css";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const SectionHeader = ({
  title,
  subtitle,
  extra,
}: {
  title: R.ReactNode;
  subtitle?: R.ReactNode;
  extra?: R.ReactNode;
}) => (
  <div className={visual.row}>
    <div>
      <div className={visual.label}>{title}</div>
      {subtitle && <div className={visual.label2}>{subtitle}</div>}
    </div>
    {extra}
  </div>
);
