import { cx } from "./cx";
import { Icon } from "./Icon";
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

/** 权限拒绝态：与错误分开——默认拒绝必须可见且可解释 */
export function ForbiddenState({ message }: { message: string }) {
  return (
    <div className={styles.state} data-testid="forbidden-state" role="status">
      <span className={cx("chip", styles.forbidden)}>
        <Icon name="lock" size={10} />
        {message}
      </span>
    </div>
  );
}

/** 能力不可用态：后端缺口/未实现——结构保留，操作禁用，原因明示（T02 pageSupport） */
export function UnavailableState({
  title,
  reason,
}: {
  title: string;
  reason: string;
}) {
  return (
    <div className={styles.unavailable} data-testid="unavailable-state" role="status">
      <div className={styles.unavailableHead}>
        <Icon name="ban" size={12} />
        <span>{title}</span>
      </div>
      <p className={styles.unavailableReason}>{reason}</p>
    </div>
  );
}

/** 数据过期/未知态：stale 与 unknown 分开呈现 */
export function StaleNotice({ message }: { message: string }) {
  return (
    <span className={cx("chip", styles.stale)} data-testid="stale-notice">
      <Icon name="clock" size={10} />
      {message}
    </span>
  );
}
