import type * as R from "react";
import type * as E from "../exampleTypes";
import visual from "./Field.module.css";
import { Icon } from "./Icon";
import { TooltipIcon } from "./TooltipIcon";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const Field = ({
  label,
  hint,
  tooltip,
  error,
  children,
  locked,
  badge,
}: {
  label: R.ReactNode;
  hint?: R.ReactNode;
  tooltip?: string;
  error?: E.ProtocolIssue | undefined;
  children: R.ReactNode;
  locked?: boolean;
  badge?: R.ReactNode;
}) => (
  <div className={visual.surface}>
    <div className={visual.row}>
      <label className={visual.label}>{label}</label>
      {tooltip && <TooltipIcon text={tooltip} />}
      {locked && <Icon name="lock" size={9} className={visual.surface2} />}
      {badge}
    </div>
    {children}
    {error && (
      <div className={visual.row2}>
        <Icon name="x" size={9} className={visual.surface3} />
        <span>
          <span className={visual.surface4}>{error.code}</span> · {error.message}
        </span>
      </div>
    )}
    {hint && !error && <div className={visual.caption}>{hint}</div>}
  </div>
);
