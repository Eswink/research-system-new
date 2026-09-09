import { useId, useRef, type ReactNode } from "react";
import { useOverlayBehavior } from "../../../components/useOverlayBehavior";
import { useExampleI18n } from "../useExampleI18n";
import visual from "./Drawer.module.css";
import { Icon } from "./Icon";

interface Props {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  subtitle?: ReactNode;
  width?: number;
  children?: ReactNode;
  footer?: ReactNode;
}

/** Closed drawers are unmounted, not hidden focusable forms outside the viewport. */
export function Drawer({ open, onClose, title, subtitle, width = 520, children, footer }: Props) {
  const panel = useRef<HTMLDivElement>(null);
  const labelId = useId();
  const { lang } = useExampleI18n();
  useOverlayBehavior(open, onClose, panel);
  if (!open) return null;
  return (
    <div className={visual.overlay}>
      <div onClick={onClose} className={visual.overlay2} />
      <div
        ref={panel}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelId}
        className={visual.column}
        style={{ width }}
      >
        <div className={visual.row}>
          <div className={visual.surface}>
            {subtitle && <div className={visual.caption}>{subtitle}</div>}
            <div id={labelId} className={visual.label}>
              {title}
            </div>
          </div>
          <button
            type="button"
            className="btn sm ghost"
            onClick={onClose}
            aria-label={lang === "zh-CN" ? "关闭抽屉" : "Close drawer"}
          >
            <Icon name="x" size={11} />
          </button>
        </div>
        <div className={visual.surface2}>{children}</div>
        {footer && <div className={visual.row2}>{footer}</div>}
      </div>
    </div>
  );
}
