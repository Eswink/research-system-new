import { useId, useRef, type ReactNode } from "react";
import { useOverlayBehavior } from "../../../components/useOverlayBehavior";
import { useExampleI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import visual from "./Modal.module.css";

interface Props {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
  width?: number;
}

export function Modal({ open, onClose, title, children, footer, width = 440 }: Props) {
  const panel = useRef<HTMLDivElement>(null);
  const labelId = useId();
  const { lang } = useExampleI18n();
  useOverlayBehavior(open, onClose, panel);
  if (!open) return null;
  return (
    <div className={visual.row} onClick={onClose}>
      <div
        ref={panel}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelId}
        onClick={(event) => {
          event.stopPropagation();
        }}
        className={visual.surface}
        style={{ width }}
      >
        <div className={visual.row2}>
          <div id={labelId} className={visual.label}>
            {title}
          </div>
          <button
            type="button"
            className={`btn sm ghost ${visual.action ?? ""}`}
            onClick={onClose}
            aria-label={lang === "zh-CN" ? "关闭对话框" : "Close dialog"}
          >
            <Icon name="x" size={11} />
          </button>
        </div>
        <div className={visual.surface2}>{children}</div>
        {footer && <div className={visual.row3}>{footer}</div>}
      </div>
    </div>
  );
}
