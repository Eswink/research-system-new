import { useId, useState, type ReactNode } from "react";

import { cx } from "./cx";
import styles from "./Tooltip.module.css";

/** 纯 CSS 定位 tooltip（hover/focus 触发）。内容简短；不承载交互控件。 */
export function Tooltip({
  content,
  children,
  side = "top",
  className,
}: {
  content: ReactNode;
  children: ReactNode;
  side?: "top" | "bottom";
  className?: string | undefined;
}) {
  const id = useId();
  const [open, setOpen] = useState(false);
  return (
    <span
      className={cx(styles.host, className)}
      onMouseEnter={() => { setOpen(true); }}
      onMouseLeave={() => { setOpen(false); }}
      onFocus={() => { setOpen(true); }}
      onBlur={() => { setOpen(false); }}
    >
      <span aria-describedby={open ? id : undefined}>{children}</span>
      {open && (
        <span role="tooltip" id={id} className={cx(styles.bubble, styles[side])}>
          {content}
        </span>
      )}
    </span>
  );
}
