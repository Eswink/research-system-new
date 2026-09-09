import { cx } from "./cx";
import styles from "./Tabs.module.css";

export interface TabItem<T extends string> {
  id: T;
  label: string;
  badge?: number | string;
}

interface Props<T extends string> {
  items: readonly TabItem<T>[];
  value: T;
  onChange: (id: T) => void;
  ariaLabel: string;
  className?: string | undefined;
}

/** Roving focus and selected state move together for arrow, Home and End navigation. */
export function Tabs<T extends string>(props: Props<T>) {
  return (
    <div
      role="tablist"
      aria-label={props.ariaLabel}
      className={cx(styles.tabs, props.className)}
      onKeyDown={(event) => {
        const target = tabTarget(props.items, props.value, event.key);
        if (target === undefined) return;
        event.preventDefault();
        props.onChange(target);
        const buttons = event.currentTarget.querySelectorAll<HTMLButtonElement>('[role="tab"]');
        [...buttons].find((button) => button.dataset.tabId === target)?.focus();
      }}
    >
      {props.items.map((item) => (
        <button
          key={item.id}
          type="button"
          role="tab"
          data-tab-id={item.id}
          aria-selected={item.id === props.value}
          tabIndex={item.id === props.value ? 0 : -1}
          className={cx(styles.tab, item.id === props.value && styles.active)}
          onClick={() => {
            props.onChange(item.id);
          }}
        >
          {item.label}
          {item.badge !== undefined && <span className={styles.badge}>{item.badge}</span>}
        </button>
      ))}
    </div>
  );
}

function tabTarget<T extends string>(items: readonly TabItem<T>[], current: T, key: string) {
  if (key === "Home") return items[0]?.id;
  if (key === "End") return items.at(-1)?.id;
  const delta = key === "ArrowRight" ? 1 : key === "ArrowLeft" ? -1 : 0;
  if (delta === 0 || items.length === 0) return undefined;
  const index = items.findIndex((item) => item.id === current);
  return items[(index + delta + items.length) % items.length]?.id;
}
