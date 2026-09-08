import { useState, type ReactNode } from "react";

import { Icon } from "./Icon";
import styles from "./Field.module.css";

function TooltipIcon({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <span
      className={styles.tooltipHost}
      onMouseEnter={() => {
        setOpen(true);
      }}
      onMouseLeave={() => {
        setOpen(false);
      }}
    >
      <button
        type="button"
        className={styles.tooltipTrigger}
        aria-label={text}
        onFocus={() => {
          setOpen(true);
        }}
        onBlur={() => {
          setOpen(false);
        }}
      >
        <Icon name="q" size={10} />
      </button>
      {open && (
        <div className={styles.tooltip} role="tooltip">
          {text}
        </div>
      )}
    </span>
  );
}

/**
 * 表单字段壳：标签 + 可选 tooltip + 错误行（E-CODE · message）或 hint 行。
 * 错误通过 aria-describedby 关联到具体输入（可访问性硬要求）。
 */
export function Field({
  label,
  htmlFor,
  hint,
  tooltip,
  error,
  locked,
  badge,
  children,
}: {
  label: string;
  htmlFor?: string | undefined;
  hint?: string | undefined;
  tooltip?: string | undefined;
  error?: { code: string; message: string } | undefined;
  locked?: boolean | undefined;
  badge?: ReactNode | undefined;
  children: ReactNode;
}) {
  const errorId = htmlFor === undefined ? undefined : `${htmlFor}-error`;
  return (
    <div className={styles.field}>
      <div className={styles.labelRow}>
        <label className={styles.label} htmlFor={htmlFor}>
          {label}
        </label>
        {tooltip !== undefined && <TooltipIcon text={tooltip} />}
        {locked === true && <Icon name="lock" size={9} className={styles.lockIcon} />}
        {badge}
      </div>
      {children}
      {error !== undefined ? (
        <div id={errorId} className={styles.errorRow} role="alert">
          <Icon name="x" size={9} className={styles.errorIcon} />
          <span>
            <span className={styles.errorCode}>{error.code}</span> · {error.message}
          </span>
        </div>
      ) : hint !== undefined ? (
        <div className={styles.hintRow}>{hint}</div>
      ) : null}
    </div>
  );
}
