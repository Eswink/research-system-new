import FIX_MEMORY from "../data/memory.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { DigestText } from "./DigestText";
import { Icon } from "./Icon";
import visual from "./MemoryTab.module.css";
import { StatusBadge } from "./StatusBadge";

/** Reference: screens/Govern.jsx; EXAMPLE ONLY. */
export const MemoryTab = () => {
  const { t } = useI18n();
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="book" size={12} className={visual.surface} />
        <span className={visual.label}>{t("gv.memWrites")}</span>
        <span className="chip">
          {FIX_MEMORY.filter((m) => m.status === "pending").length} {t("gv.memPending")}
        </span>
        <span className={visual.label2}>{t("gv.memHint")}</span>
      </div>
      <MemoryTabApprove {...{ t }} />
    </div>
  );
};

interface MemoryTabApproveProps {
  t: (key: string, fallback?: string) => string;
}

function MemoryTabApprove({ t }: MemoryTabApproveProps) {
  return (
    <div className={visual.grid}>
      {FIX_MEMORY.map((m) => (
        <div
          key={m.id}
          className={`panel ${visual.panel2 ?? ""}`}
          style={{
            background: m.status === "approved" ? "var(--success-dim)" : "var(--bg-raised)",
            border: `1px solid ${
              m.status === "approved" ? "var(--success-line)" : "var(--border)"
            }`,
          }}
        >
          <MemoryTabApprove2 {...{ m, t }} />
          <div className={visual.label3}>{m.statement}</div>
          <div className={visual.caption2}>
            {t("gv.provenance")} {m.provenance.slice(0, 2).join(" · ")}
            {m.provenance.length > 2 ? ` +${String(m.provenance.length - 2)}` : ""}
          </div>
          <div className={visual.row3}>
            <button className={`btn sm ${visual.action ?? ""}`} disabled={m.status === "approved"}>
              <Icon name="check" size={10} /> {t("act.approve")}
            </button>
            <button className={`btn sm ${visual.action2 ?? ""}`} disabled={m.status === "approved"}>
              <Icon name="x" size={10} /> {t("act.reject")}
            </button>
            <button className={`btn sm ghost ${visual.action3 ?? ""}`} title={t("gv.deleteReal")}>
              <Icon name="ban" size={10} /> {t("act.delete")}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

interface MemoryTabApprove2Props {
  m:
    | {
        id: string;
        statement: string;
        scope: string;
        confidence: number;
        provenance: string[];
        expires_at: string;
        status: string;
      }
    | {
        id: string;
        statement: string;
        scope: string;
        confidence: number;
        provenance: string[];
        expires_at: null;
        status: string;
      };
  t: (key: string, fallback?: string) => string;
}

function MemoryTabApprove2({ m, t }: MemoryTabApprove2Props) {
  return (
    <div className={visual.row2}>
      <span
        className="chip"
        style={{
          color: m.scope === "org" ? "var(--accent)" : "var(--fg-muted)",
          borderColor: m.scope === "org" ? "var(--accent-line)" : "var(--border)",
        }}
      >
        {m.scope}
      </span>
      <span className={`mono ${visual.caption ?? ""}`}>
        {t("gv.confidence")} {m.confidence.toFixed(2)}
      </span>
      {m.status === "approved" && (
        <StatusBadge
          tone="success"
          icon="check"
          label={t("act.approve").toUpperCase()}
          filled
          size="sm"
        />
      )}
      <DigestText value={m.id} length={6} prefix={false} />
    </div>
  );
}
