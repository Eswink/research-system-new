import type { ReactNode } from "react";
import styles from "./PageHeader.module.css";

/** Live and example pages share the handoff's compact kicker/title/action hierarchy. */
export function PageHeader({
  title,
  kicker,
  description,
  actions,
}: {
  title: string;
  kicker: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className={styles.header}>
      <div className={styles.identity}>
        <div className={styles.kicker}>{kicker}</div>
        <h1 className={styles.title}>{title}</h1>
        {description !== undefined && <p className={styles.description}>{description}</p>}
      </div>
      {actions !== undefined && <div className={styles.actions}>{actions}</div>}
    </header>
  );
}
