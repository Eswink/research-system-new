import type * as E from "../exampleTypes";
import visual from "./EmptyState.module.css";
import { Icon } from "./Icon";

/** Reference: components/patterns.jsx; EXAMPLE ONLY. */
export const EmptyState = ({
  icon = "diamond",
  title,
  description,
  cta,
  secondaryCta,
  kicker,
}: {
  icon?: string;
  title: string;
  description: string;
  cta?: E.Cta;
  secondaryCta?: E.Cta;
  kicker?: string;
}) => (
  <div className={visual.column}>
    <div className={visual.row}>
      <Icon name={icon} size={22} />
    </div>
    {kicker && <div className={visual.caption}>{kicker}</div>}
    <div className={visual.label}>{title}</div>
    {description && <div className={visual.label2}>{description}</div>}
    {(cta ?? secondaryCta) && (
      <div className={visual.row2}>
        {cta && (
          <button className="btn primary" onClick={cta.onClick}>
            {cta.icon && <Icon name={cta.icon} size={11} />} {cta.label}
          </button>
        )}
        {secondaryCta && (
          <button className="btn" onClick={secondaryCta.onClick}>
            {secondaryCta.icon && <Icon name={secondaryCta.icon} size={11} />} {secondaryCta.label}
          </button>
        )}
      </div>
    )}
  </div>
);
