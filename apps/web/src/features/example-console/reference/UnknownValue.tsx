import { Icon } from "./Icon";
import visual from "./UnknownValue.module.css";

/** Reference: components/atoms.jsx; EXAMPLE ONLY. */
export const UnknownValue = ({ hint = "estimated_cost_minor=null" }: { hint?: string }) => (
  <span title={hint} className={visual.row}>
    <Icon name="q" size={10} /> UNKNOWN
  </span>
);
