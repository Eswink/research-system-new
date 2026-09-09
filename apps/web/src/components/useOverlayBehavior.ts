import { useEffect, useRef } from "react";

const panels: HTMLElement[] = [];

/** Only the top overlay traps focus. Rerendering a callback never steals input focus. */
export function useOverlayBehavior(
  open: boolean,
  onClose: () => void,
  panelRef: React.RefObject<HTMLElement | null>,
): void {
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const panel = panelRef.current;
    if (!open || panel === null) return;
    const restore = document.activeElement;
    panels.push(panel);
    panel.focus();
    const onKey = (event: KeyboardEvent): void => {
      if (panels.at(-1) !== panel) return;
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        close.current();
      } else if (event.key === "Tab") trapFocus(event, panel);
    };
    document.addEventListener("keydown", onKey, true);
    return () => {
      document.removeEventListener("keydown", onKey, true);
      const top = panels.at(-1) === panel;
      const index = panels.lastIndexOf(panel);
      if (index >= 0) panels.splice(index, 1);
      if (top && restore instanceof HTMLElement && restore.isConnected) restore.focus();
    };
  }, [open, panelRef]);
}

function trapFocus(event: KeyboardEvent, container: HTMLElement): void {
  const candidates = container.querySelectorAll<HTMLElement>(
    'a[href], button, textarea, input:not([type="hidden"]), select, [tabindex]',
  );
  const focusables = [...candidates].filter(
    (element) =>
      element.tabIndex >= 0 &&
      !element.matches(":disabled, [hidden], [inert]") &&
      element.getClientRects().length > 0,
  );
  const first = focusables[0];
  const last = focusables.at(-1);
  if (first === undefined || last === undefined) {
    event.preventDefault();
    container.focus();
    return;
  }
  const active = document.activeElement;
  if (!container.contains(active) || active === container) {
    event.preventDefault();
    (event.shiftKey ? last : first).focus();
  } else if (event.shiftKey && active === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus();
  }
}
