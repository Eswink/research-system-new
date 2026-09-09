import FIX_APPROVALS from "../data/approvals.json";
import FIX_BUDGET from "../data/budget.json";
import FIX_CLAIMS from "../data/claims.json";
import FIX_EVIDENCE from "../data/evidence.json";
import FIX_RUN from "../data/run.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { BundleStat } from "./BundleStat";
import { DigestText } from "./DigestText";
import visual from "./ExportTab.module.css";
import { Icon } from "./Icon";
import { RunStateBadge } from "./RunStateBadge";

/** Reference: screens/Govern.jsx; EXAMPLE ONLY. */
export const ExportTab = () => {
  const { t } = useI18n();
  const evidenceCount = FIX_EVIDENCE.length;
  const claimCount = FIX_CLAIMS.length;
  const usageEntries = FIX_BUDGET.reservations.length;
  const unknownEntries = FIX_BUDGET.unknown_cost_entries;

  return (
    <div className={visual.grid}>
      {/* Bundle preview */}
      <ExportTabClaims {...{ t, claimCount, evidenceCount, usageEntries, unknownEntries }} />

      {/* Warnings */}
      <div className={visual.column}>
        <div className={`panel ${visual.panel2 ?? ""}`}>
          <div className={visual.caption3}>{t("gv.summary")}</div>
          <div className={visual.column2}>
            <div className={visual.row3}>
              <Icon name="check" size={12} className={visual.surface12} /> {t("gv.sum1")}
            </div>
            <div className={visual.row4}>
              <Icon name="warn-tri" size={12} className={visual.surface13} /> {t("gv.sum2")}
            </div>
            <div className={visual.row5}>
              <Icon name="q" size={12} className={visual.surface14} /> {t("gv.sum3")}{" "}
              <span className="mono">reproduction_available=false</span>
              {t("gv.sum3b")}
            </div>
            <div className={visual.row6}>
              <Icon name="q" size={12} className={visual.surface15} /> {t("gv.sum4")}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

interface ExportTabClaimsProps {
  t: (key: string, fallback?: string) => string;
  claimCount: number;
  evidenceCount: number;
  usageEntries: number;
  unknownEntries: number;
}

function ExportTabClaims({
  t,
  claimCount,
  evidenceCount,
  usageEntries,
  unknownEntries,
}: ExportTabClaimsProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="external" size={12} className={visual.surface} />
        <span className={visual.label}>{t("gv.exportPreview")}</span>
      </div>
      <ExportTabClaims2 {...{ t, claimCount, evidenceCount, usageEntries, unknownEntries }} />
      <div className={visual.row2}>
        <button className={`btn primary ${visual.action ?? ""}`}>
          <Icon name="external" size={11} /> {t("gv.exportSealed")}
        </button>
        <button className="btn">
          <Icon name="copy" size={11} /> {t("gv.copyManifest")}
        </button>
      </div>
    </div>
  );
}

interface ExportTabClaims2Props {
  t: (key: string, fallback?: string) => string;
  claimCount: number;
  evidenceCount: number;
  usageEntries: number;
  unknownEntries: number;
}

function ExportTabClaims2({
  t,
  claimCount,
  evidenceCount,
  usageEntries,
  unknownEntries,
}: ExportTabClaims2Props) {
  return (
    <div className={visual.surface2}>
      <div className={visual.grid2}>
        <span className={visual.surface3}>run_id</span>{" "}
        <DigestText value={FIX_RUN.id} length={22} prefix={false} />
        <span className={visual.surface4}>run_state</span> <RunStateBadge state="RUNNING" />
        <span className={visual.surface5}>manifest_digest</span>{" "}
        <DigestText value={FIX_RUN.manifest_digest} length={16} />
        <span className={visual.surface6}>protocol_digest</span>{" "}
        <DigestText value={FIX_RUN.protocol_digest} length={16} />
        <span className={visual.surface7}>exported_from</span>{" "}
        <span className={`mono ${visual.label2 ?? ""}`}>console.researchos.io · v1.4.2</span>
        <span className={visual.surface8}>exported_at</span>{" "}
        <span className={`mono ${visual.label3 ?? ""}`}>2026-08-27T14:44:03Z</span>
      </div>

      <div className={`hr ${visual.surface9 ?? ""}`} />

      <div className={visual.caption}>{t("gv.contents")}</div>
      <ExportTabClaims3 {...{ t, claimCount, evidenceCount, usageEntries, unknownEntries }} />

      <div className={`hr ${visual.surface11 ?? ""}`} />

      <div className={visual.caption2}>{t("gv.integrity")}</div>
      <div className={visual.label4}>{t("gv.integrityMsg")}</div>
    </div>
  );
}

interface ExportTabClaims3Props {
  t: (key: string, fallback?: string) => string;
  claimCount: number;
  evidenceCount: number;
  usageEntries: number;
  unknownEntries: number;
}

function ExportTabClaims3({
  t,
  claimCount,
  evidenceCount,
  usageEntries,
  unknownEntries,
}: ExportTabClaims3Props) {
  return (
    <div className={visual.grid3}>
      <BundleStat
        label={t("gv.claims")}
        value={claimCount}
        sub={`${String(FIX_CLAIMS.filter((c) => c.status === "VERIFIED").length)} ${t(
          "gv.claimsSub",
        )} ${String(FIX_CLAIMS.filter((c) => c.status === "PROPOSED").length)} ${t(
          "gv.claimsSub2",
        )}`}
      />
      <BundleStat
        label={t("gv.evidenceEntries")}
        value={evidenceCount}
        sub={`${String(FIX_EVIDENCE.filter((e) => e.kind === "experiment").length)} ${t(
          "gv.evidenceExp",
        )} ${String(FIX_EVIDENCE.filter((e) => e.kind === "literature").length)} ${t(
          "gv.evidenceLit",
        )}`}
      />
      <BundleStat
        label={t("gv.usageEntries")}
        value={usageEntries}
        sub={
          <span className={visual.surface10}>
            {unknownEntries} {t("gv.usageEntriesSub")}
          </span>
        }
        unknown
      />
      <BundleStat
        label={t("gv.approvalsDecided")}
        value={FIX_APPROVALS.length}
        sub={t("gv.approvalsSub")}
      />
    </div>
  );
}
