import { useState } from "react";
import { Icon } from "./Icon";
import visual from "./TooltipIcon.module.css";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const TooltipIcon = ({ text }: { text: string }) => {
  const [open, setOpen] = useState(false);
  return (
    <span
      className={visual.surface}
      onMouseEnter={() => {
        setOpen(true);
      }}
      onMouseLeave={() => {
        setOpen(false);
      }}
    >
      <Icon name="q" size={10} className={visual.surface2} />
      {open && <div className={visual.label}>{text}</div>}
    </span>
  );
};
