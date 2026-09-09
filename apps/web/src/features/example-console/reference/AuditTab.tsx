import FIX_AUDIT from "../data/audit.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./AuditTab.module.css";
import { DigestText } from "./DigestText";
import { Icon } from "./Icon";

/** Reference: screens/Govern.jsx; EXAMPLE ONLY. */
export const AuditTab = () => {
  const { t } = useI18n();
  return <AuditTabSection {...{ t }} />;
};

interface AuditTabSectionProps {
  t: (key: string, fallback?: string) => string;
}

function AuditTabSection({ t }: AuditTabSectionProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="menu" size={12} className={visual.surface} />
        <span className={visual.label}>{t("gv.auditTrail")}</span>
        <span className="chip">{FIX_AUDIT.length}</span>
        <span className={visual.caption}>
          <Icon name="eye-off" size={10} /> {t("gv.redacted")}
        </span>
      </div>
      <AuditTabSection2 {...{ t }} />
    </div>
  );
}

interface AuditTabSection2Props {
  t: (key: string, fallback?: string) => string;
}

function AuditTabSection2({ t }: AuditTabSection2Props) {
  return (
    <div className={visual.surface2}>
      <div className={`row head ${visual.surface3 ?? ""}`}>
        <span>{t("lbl.time")}</span>
        <span>{t("lbl.scope")}</span>
        <span>{t("lbl.actor")}</span>
        <span>{t("lbl.verbSubject")}</span>
        <span>{t("lbl.digest")}</span>
        <span></span>
      </div>
      {FIX_AUDIT.map((a) => (
        <div key={a.id} className={`row ${visual.surface4 ?? ""}`}>
          <span className={visual.label2}>{a.occurred_at.replace("T", " ").slice(0, 19)}</span>
          <span className="chip">{a.scope}</span>
          <span
            className={visual.label3}
            style={{
              color:
                a.actor.kind === "user"
                  ? "var(--accent)"
                  : a.actor.kind === "policy"
                    ? "var(--unknown)"
                    : "var(--fg-muted)",
            }}
          >
            <Icon
              name={
                a.actor.kind === "user" ? "circle" : a.actor.kind === "policy" ? "shield" : "hex"
              }
              size={9}
            />{" "}
            {a.actor.kind}
            {a.actor.id ? ":" + a.actor.id.slice(0, 10) : ""}
          </span>
          <span className={visual.label4}>
            <span className={`mono ${visual.surface5 ?? ""}`}>{a.verb}</span>
            <span className={visual.surface6}>→ {a.subject_ref}</span>
          </span>
          <DigestText value={a.digest} length={8} />
          <button className="btn sm ghost">
            <Icon name="external" size={10} /> {t("act.jump")}
          </button>
        </div>
      ))}
    </div>
  );
}
