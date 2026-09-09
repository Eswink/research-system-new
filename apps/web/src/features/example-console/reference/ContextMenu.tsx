import { useEffect } from "react";
import type * as E from "../exampleTypes";
import visual from "./ContextMenu.module.css";
import { Icon } from "./Icon";

/** Reference: components/patterns.jsx; EXAMPLE ONLY. */
export const ContextMenu = ({
  x,
  y,
  items,
  onClose,
}: {
  x: number;
  y: number;
  items: E.MenuItem[];
  onClose: () => void;
}) => {
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", h);
    document.addEventListener("click", onClose, { once: true });
    return () => {
      document.removeEventListener("keydown", h);
    };
  }, [onClose]);
  return <ContextMenuOverlay {...{ x, y, items, onClose }} />;
};

interface ContextMenuOverlayProps {
  x: number;
  y: number;
  items: E.MenuItem[];
  onClose: () => void;
}

function ContextMenuOverlay({ x, y, items, onClose }: ContextMenuOverlayProps) {
  return (
    <div className={visual.overlay} style={{ left: x, top: y }}>
      {items.map((it, i) => {
        if (it.divider) return <div key={i} className={visual.indicator} />;
        return (
          <button
            key={i}
            onClick={() => {
              it.action?.();
              onClose();
            }}
            disabled={it.disabled}
            className={visual.row}
            style={{
              color: it.danger ? "var(--danger)" : "var(--fg)",
              opacity: it.disabled ? 0.4 : 1,
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-hover)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            {it.icon && <Icon name={it.icon} size={11} />}
            <span className={visual.surface}>{it.label}</span>
            {it.shortcut && <kbd>{it.shortcut}</kbd>}
          </button>
        );
      })}
    </div>
  );
}
