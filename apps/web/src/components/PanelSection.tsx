import { useId, type ReactNode } from "react";

import { Icon, type IconName } from "./Icon";
import styles from "./PanelSection.module.css";

/** 标准面板区块：标题 + 计数 chip + 右侧 extra 插槽 + 内容 */
export function PanelSection({
  icon,
  title,
  count,
  extra,
  children,
}: {
  icon?: IconName | undefined;
  title: string;
  count?: number | undefined;
  extra?: ReactNode | undefined;
  children: ReactNode;
}) {
  const headingId = useId();
  return (
    <section className={styles.section} aria-labelledby={headingId}>
      <header className={styles.header}>
        {icon !== undefined && <Icon name={icon} size={12} className={styles.icon} />}
        <span id={headingId} className={styles.title}>
          {title}
        </span>
        {count !== undefined && <span className="chip">{String(count)}</span>}
        {extra !== undefined && <span className={styles.extra}>{extra}</span>}
      </header>
      <div className={styles.body}>{children}</div>
    </section>
  );
}
