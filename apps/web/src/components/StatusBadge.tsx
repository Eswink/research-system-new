import { cx } from "./cx";
import { Icon, type IconName } from "./Icon";
import styles from "./StatusBadge.module.css";

export type StatusTone = "success" | "warn" | "danger" | "accent" | "unknown" | "neutral";

const TONE_ICONS: Partial<Record<StatusTone, IconName>> = {
  success: "check",
  warn: "warn-tri",
  danger: "x",
  unknown: "q",
};

/**
 * 状态徽章：文字 + 图标 + 形状 + 颜色四重编码（P4：不确定 ≠ 零）。
 * 仅颜色单通道的状态展示不通过此组件实现。
 */
export function StatusBadge({
  tone,
  label,
  icon,
}: {
  tone: StatusTone;
  label: string;
  icon?: IconName | undefined;
}) {
  const fallback = TONE_ICONS[tone];
  const resolved: IconName | undefined = icon ?? fallback;
  const toneClass: string = styles[tone] ?? "";
  return (
    <span className={cx(styles.badge, toneClass)} data-tone={tone}>
      {resolved !== undefined && <Icon name={resolved} size={10} />}
      <span>{label}</span>
    </span>
  );
}
