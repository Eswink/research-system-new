import { useRef, type ReactNode } from "react";

import { Icon } from "./Icon";
import styles from "./Overlay.module.css";
import { useOverlayBehavior } from "./useOverlayBehavior";

/** 右侧抽屉：Escape 关闭、焦点约束与返回（useOverlayBehavior）。 */
export function Drawer({
  open,
  onClose,
  title,
  subtitle,
  width = 520,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string | undefined;
  width?: number;
  children: ReactNode;
  footer?: ReactNode | undefined;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  useOverlayBehavior(open, onClose, panelRef);
  return (
    <div
      className={styles.scrimHost}
      style={{ pointerEvents: open ? "auto" : "none" }}
      aria-hidden={!open}
    >
      <div className={styles.scrim} style={{ opacity: open ? 1 : 0 }} onClick={onClose} />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className={styles.drawer}
        style={{ width, maxWidth: "94vw", transform: open ? "translateX(0)" : "translateX(100%)" }}
      >
        <div className={styles.head}>
          <div className={styles.headText}>
            {subtitle !== undefined && <div className={styles.subtitle}>{subtitle}</div>}
            <div className={styles.title}>{title}</div>
          </div>
          <button type="button" className="btn sm ghost" onClick={onClose} aria-label="Close">
            <Icon name="x" size={11} />
          </button>
        </div>
        <div className={styles.body}>{children}</div>
        {footer !== undefined && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>
  );
}
