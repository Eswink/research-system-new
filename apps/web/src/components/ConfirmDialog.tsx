import { useRef, type ReactNode } from "react";

import { Button } from "./Button";
import { Icon } from "./Icon";
import styles from "./Overlay.module.css";
import { useOverlayBehavior } from "./useOverlayBehavior";

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  consequence: ReactNode;
  confirmLabel: string;
  cancelLabel: string;
  danger?: boolean;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  extra?: ReactNode;
}

/** 后果确认对话框：高风险操作必须经此确认；调用方处理服务端结果。 */
export function ConfirmDialog(props: ConfirmDialogProps) {
  const { open, title, danger = false, busy = false, onCancel } = props;
  const dialogRef = useRef<HTMLDivElement>(null);
  const requestClose = busy ? () => undefined : onCancel;
  useOverlayBehavior(open, requestClose, dialogRef);
  if (!open) {
    return null;
  }
  return (
    <div className={styles.modalScrim} onClick={requestClose}>
      <div
        ref={dialogRef}
        role="alertdialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className={styles.modal}
        style={{ width: 440 }}
        onClick={(event) => { event.stopPropagation(); }}
      >
        <div className={styles.modalHead}>
          <Icon name={danger ? "warn-tri" : "q"} size={13} />
          <div className={styles.modalTitle}>{title}</div>
        </div>
        <div className={styles.modalBody}>
          {props.consequence}
          {props.extra}
        </div>
        <ConfirmFooter {...props} />
      </div>
    </div>
  );
}

function ConfirmFooter({
  cancelLabel,
  confirmLabel,
  danger = false,
  busy = false,
  onCancel,
  onConfirm,
}: ConfirmDialogProps) {
  return (
    <div className={styles.modalFooter}>
      <Button variant="ghost" onClick={onCancel} disabled={busy}>{cancelLabel}</Button>
      <Button
        variant={danger ? "danger" : "primary"}
        onClick={onConfirm}
        disabled={busy}
        data-testid="confirm-dialog-confirm"
      >
        {busy ? "…" : confirmLabel}
      </Button>
    </div>
  );
}
