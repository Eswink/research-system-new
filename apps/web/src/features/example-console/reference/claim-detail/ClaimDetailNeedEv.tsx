import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ClaimDetail.module.css";
import { ClaimStatusBadge } from "../ClaimStatusBadge";
import { DigestText } from "../DigestText";
import { Icon } from "../Icon";
import { ClaimDetailSection } from "./ClaimDetailSection";

interface ClaimDetailNeedEvProps {
  claim: FixtureTypes.Claim;
  isProposed: boolean;
  t: (key: string, fallback?: string) => string;
  supports: FixtureTypes.Evidence[];
  refutes: FixtureTypes.Evidence[];
}

export function ClaimDetailNeedEv({
  claim,
  isProposed,
  t,
  supports,
  refutes,
}: ClaimDetailNeedEvProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <ClaimDetailNeedEvSurface {...{ claim, isProposed }} />

      <ClaimDetailSection {...{ isProposed, claim, t, supports, refutes }} />

      {claim.status === "PROPOSED" && (
        <div className={visual.surface6}>
          <div className={visual.caption}>{t("cl.upgradePath")}</div>
          <div className={visual.label6}>
            {t("cl.upgradeMsg").split("{a}")[0]}
            <span className={`mono ${visual.surface7 ?? ""}`}>promote_claim_to_verified</span>
            {t("cl.upgradeMsg").split("{a}")[1]}
          </div>
          <button className="btn sm" disabled aria-disabled="true" title={t("cl.needEv")}>
            <Icon name="lock" size={10} /> {t("cl.requestUpgrade")}
          </button>
        </div>
      )}
    </div>
  );
}

interface ClaimDetailNeedEvSurfaceProps {
  claim:
    | {
        id: string;
        statement: string;
        status: string;
        evidence_count: number;
        source_count: number;
        updated_at: string;
        owner: string;
        dispute_note?: never;
        refutation_note?: never;
      }
    | {
        id: string;
        statement: string;
        status: string;
        evidence_count: number;
        source_count: number;
        updated_at: string;
        owner?: never;
        dispute_note?: never;
        refutation_note?: never;
      }
    | {
        id: string;
        statement: string;
        status: string;
        evidence_count: number;
        source_count: number;
        dispute_note: string;
        updated_at: string;
        owner?: never;
        refutation_note?: never;
      }
    | {
        id: string;
        statement: string;
        status: string;
        evidence_count: number;
        source_count: number;
        refutation_note: string;
        updated_at: string;
        owner?: never;
        dispute_note?: never;
      };
  isProposed: boolean;
}

function ClaimDetailNeedEvSurface({ claim, isProposed }: ClaimDetailNeedEvSurfaceProps) {
  return (
    <div className={visual.surface}>
      <div className={visual.row}>
        <ClaimStatusBadge status={claim.status} />
        <DigestText value={claim.id} length={12} prefix={false} />
      </div>
      <div
        className={visual.label}
        style={{
          color: isProposed ? "var(--fg-muted)" : "var(--fg)",
          fontStyle: isProposed ? "italic" : "normal",
        }}
      >
        {claim.statement}
      </div>
      {claim.dispute_note && (
        <div className={visual.label2}>
          <Icon name="warn-tri" size={10} /> {claim.dispute_note}
        </div>
      )}
      {claim.refutation_note && (
        <div className={visual.label3}>
          <Icon name="x" size={10} /> {claim.refutation_note}
        </div>
      )}
    </div>
  );
}
