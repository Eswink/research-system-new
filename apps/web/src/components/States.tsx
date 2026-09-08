import { cx } from "./cx";
import styles from "./States.module.css";

/** 空态：明确"无数据"，永不冒充零值（P4） */
export function EmptyState({ message }: { message: string }) {
  return (
    <div className={styles.state} data-testid="empty-state">
      <span className="empty-mark">{message}</span>
    </div>
  );
}

/** 加载态 */
export function LoadingState({ message }: { message: string }) {
  return (
    <div className={styles.state} data-testid="loading-state" role="status">
      <span className="chip">{message}</span>
    </div>
  );
}

/** 错误态：role=alert；403 单独识别（P5 默认拒绝要可见） */
export function ErrorState({ message }: { message: string }) {
  return (
    <div className={cx(styles.state, styles.error)} data-testid="error-state" role="alert">
      <span className="chip">{message}</span>
    </div>
  );
}
