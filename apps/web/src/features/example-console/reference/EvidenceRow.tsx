import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { DigestText } from "./DigestText";
import visual from "./EvidenceRow.module.css";
import { Icon } from "./Icon";

/** Reference: screens/Claims.jsx; EXAMPLE ONLY. */
export const EvidenceRow = ({ ev }: { ev: E.Evidence }) => {
  const { t } = useI18n();
  const kindIcon =
    ev.kind === "literature" ? "book" : ev.kind === "experiment" ? "flask" : "square";
  const kindColor =
    ev.kind === "literature"
      ? "var(--accent)"
      : ev.kind === "experiment"
        ? "var(--warn)"
        : "var(--fg-muted)";
  return (
    <div className={visual.surface}>
      <div className={visual.row}>
        <Icon name={kindIcon} size={11} style={{ color: kindColor }} />
        <span className={visual.label} style={{ color: kindColor }}>
          {ev.kind}
        </span>
        <span className={visual.caption}>
          {t("cl.evStrength")} {ev.strength.toFixed(2)}
        </span>
      </div>
      <div className={visual.label2}>{ev.source_ref}</div>
      <div className={visual.row2}>
        <DigestText value={ev.content_digest} label="content:" length={8} />
        {ev.image_digest && <DigestText value={ev.image_digest} label="image:" length={8} />}
        {ev.environment_digest && (
          <DigestText value={ev.environment_digest} label="env:" length={8} />
        )}
      </div>
    </div>
  );
};
