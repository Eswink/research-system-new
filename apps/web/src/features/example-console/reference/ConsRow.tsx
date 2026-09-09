import type * as R from "react";
import visual from "./ConsRow.module.css";
import { Icon } from "./Icon";

/** Reference: screens/Approvals.jsx; EXAMPLE ONLY. */
export const ConsRow = ({
  icon,
  tone,
  label,
}: {
  icon: string;
  tone: string;
  label: R.ReactNode;
}) => (
  <li className={visual.row}>
    <Icon
      name={icon}
      size={11}
      style={{
        color: `var(--${tone === "success" ? "success" : tone === "warn" ? "warn" : "danger"})`,
      }}
    />
    <span className={visual.surface}>{label}</span>
  </li>
);
