import type * as R from "react";
import visual from "./Panel.module.css";

/** Reference: Command Center.html; every metric is a fixed example. */
export const Panel = ({
  kicker,
  title,
  right,
  children,
  style,
  className,
}: {
  kicker: string;
  title: string;
  right?: R.ReactNode;
  children: R.ReactNode;
  style?: R.CSSProperties;
  className?: string | undefined;
}) => (
  <div className={["cc-panel", className].filter(Boolean).join(" ")} style={style}>
    <div className="cc-panel-header">
      <span className="kicker">■</span>
      <span className={visual.surface}>{kicker}</span>
      <span className={visual.surface2}>· {title}</span>
      {right && <div className={visual.row}>{right}</div>}
    </div>
    <div className="cc-panel-body">{children}</div>
  </div>
);
