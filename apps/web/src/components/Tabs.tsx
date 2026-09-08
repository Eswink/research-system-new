import { cx } from "./cx";
import styles from "./Tabs.module.css";

export interface TabItem<T extends string> {
  id: T;
  label: string;
  badge?: number | string;
}

function nextTab<T extends string>(
  items: readonly TabItem<T>[],
  value: T,
  delta: number,
): T | null {
  const idx = items.findIndex((item) => item.id === value);
  const next = items[(idx + delta + items.length) % items.length];
  return next === undefined ? null : next.id;
}

/** 页内二级标签（视图切换、Tab 区）。键盘：左右箭头移动焦点。 */
export function Tabs<T extends string>({
  items,
  value,
  onChange,
  ariaLabel,
  className,
}: {
  items: readonly TabItem<T>[];
  value: T;
  onChange: (id: T) => void;
  ariaLabel: string;
  className?: string | undefined;
}) {
  const onKeyDown = (event: React.KeyboardEvent): void => {
    const delta = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (delta === 0) {
      return;
    }
    event.preventDefault();
    const target = nextTab(items, value, delta);
    if (target !== null) {
      onChange(target);
    }
  };
  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className={cx(styles.tabs, className)}
      onKeyDown={onKeyDown}
    >
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          role="tab"
          aria-selected={item.id === value}
          tabIndex={item.id === value ? 0 : -1}
          className={cx(styles.tab, item.id === value && styles.active)}
          onClick={() => { onChange(item.id); }}
        >
          {item.label}
          {item.badge !== undefined && <span className={styles.badge}>{item.badge}</span>}
        </button>
      ))}
    </div>
  );
}
