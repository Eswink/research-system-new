import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ClaimDetail.module.css";
import { EvidenceRow } from "../EvidenceRow";
import { Icon } from "../Icon";

interface ClaimDetailSectionProps {
  isProposed: boolean;
  claim: FixtureTypes.Claim;
  t: (key: string, fallback?: string) => string;
  supports: FixtureTypes.Evidence[];
  refutes: FixtureTypes.Evidence[];
}

export function ClaimDetailSection({
  isProposed,
  claim,
  t,
  supports,
  refutes,
}: ClaimDetailSectionProps) {
  return (
    <div className={visual.surface2}>
      {isProposed && claim.evidence_count === 0 && (
        <div className={visual.surface3}>
          <div className={visual.label4}>
            <Icon name="circle-dash" size={12} /> {t("cl.noEvidence")}
          </div>
          <div className={visual.label5}>
            {t("cl.awaitingEv").replace("{a}", "").split("PROPOSED")[0]}
            <span className="mono">ag_pi_01</span>
            {t("cl.awaitingEv").split("{a}")[1]}
          </div>
        </div>
      )}

      {supports.length > 0 && (
        <>
          <div className={visual.row2}>
            <span>
              {t("cl.supporting")} {supports.length}
            </span>
            <span className={visual.surface4}>SUPPORTS</span>
          </div>
          {supports.map((ev) => (
            <EvidenceRow key={ev.id} ev={ev} />
          ))}
        </>
      )}

      {refutes.length > 0 && (
        <>
          <div className={visual.row3}>
            <span>
              {t("cl.refuting")} {refutes.length}
            </span>
            <span className={visual.surface5}>REFUTES</span>
          </div>
          {refutes.map((ev) => (
            <EvidenceRow key={ev.id} ev={ev} />
          ))}
        </>
      )}
    </div>
  );
}
