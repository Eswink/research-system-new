import type * as E from "../exampleTypes";
import type * as FixtureTypes from "../fixtureTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./ClaimsTable.module.css";
import { ClaimStatusBadge } from "./ClaimStatusBadge";
import { DigestText } from "./DigestText";

/** Reference: screens/Claims.jsx; EXAMPLE ONLY. */
export const ClaimsTable = ({
  claims,
  selectedId,
  onSelect,
}: {
  claims: E.Claim[];
  selectedId: string;
  onSelect: (id: string) => void;
}) => {
  const { t } = useI18n();
  return <ClaimsTableSection {...{ t, claims, selectedId, onSelect }} />;
};

interface ClaimsTableSectionProps {
  t: (key: string, fallback?: string) => string;
  claims: FixtureTypes.Claim[];
  selectedId: string;
  onSelect: (id: string) => void;
}

function ClaimsTableSection({ t, claims, selectedId, onSelect }: ClaimsTableSectionProps) {
  return (
    <div>
      <div className={`row head ${visual.surface ?? ""}`}>
        <span>{t("lbl.status")}</span>
        <span>{t("cl.tHead.statement")}</span>
        <span>{t("cl.tHead.id")}</span>
        <span>{t("cl.tHead.ev")}</span>
        <span>{t("cl.tHead.src")}</span>
        <span>{t("lbl.updated")}</span>
      </div>
      {claims.map((claim) => (
        <ClaimTableRow key={claim.id} {...{ claim, selectedId, onSelect }} />
      ))}
    </div>
  );
}

interface ClaimTableRowProps {
  claim: FixtureTypes.Claim;
  selectedId: string;
  onSelect: (id: string) => void;
}

function ClaimTableRow({ claim, selectedId, onSelect }: ClaimTableRowProps) {
  const proposed = claim.status === "PROPOSED";
  return (
    <div
      className={`row ${visual.surface2 ?? ""}`}
      style={{
        background: claim.id === selectedId ? "var(--bg-hover)" : undefined,
        opacity: proposed ? 0.75 : 1,
      }}
      onClick={() => {
        onSelect(claim.id);
      }}
    >
      <ClaimStatusBadge status={claim.status} />
      <span
        className={visual.label}
        style={{
          fontStyle: proposed ? "italic" : "normal",
          color: proposed ? "var(--fg-muted)" : "var(--fg)",
        }}
      >
        {claim.statement}
      </span>
      <DigestText value={claim.id} length={8} prefix={false} />
      <ClaimCount value={claim.evidence_count} className={visual.label2} />
      <ClaimCount value={claim.source_count} className={visual.label3} />
      <span className={visual.caption}>{claim.updated_at.slice(5, 16).replace("T", " ")}</span>
    </div>
  );
}

function ClaimCount({ value, className }: { value: number; className: string | undefined }) {
  return (
    <span
      className={className}
      style={{ color: value === 0 ? "var(--unknown)" : "var(--fg-muted)" }}
    >
      {value === 0 ? "0*" : value}
    </span>
  );
}
