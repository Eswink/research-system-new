import type { ReactNode } from "react";

import { cx } from "./cx";
import { Icon, type IconName } from "./Icon";
import styles from "./Chip.module.css";

/** 轻量 chip：等宽小标签（mono）。tone 仅影响颜色，文字始终在场。 */
export function Chip({
  children,
  icon,
  tone = "neutral",
  dashed = false,
  className,
  title,
}: {
  children: ReactNode;
  icon?: IconName;
  tone?: "neutral" | "accent" | "success" | "warn" | "danger" | "unknown";
  dashed?: boolean;
  className?: string | undefined;
  title?: string | undefined;
}) {
  return (
    <span
      className={cx("chip", styles[tone], dashed && styles.dashed, className)}
      title={title}
    >
      {icon !== undefined && <Icon name={icon} size={10} />}
      {children}
    </span>
  );
}
