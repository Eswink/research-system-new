import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ApprovalCard.module.css";
import { DigestText } from "../DigestText";
import { GateChip } from "../GateChip";
import { StatusBadge } from "../StatusBadge";

interface ApprovalCardSection3Props {
  approval: FixtureTypes.Approval;
  riskTone: string;
}

export function ApprovalCardSection3({ approval, riskTone }: ApprovalCardSection3Props) {
  return (
    <div className={visual.row}>
      <GateChip type={approval.policy_source} />
      <StatusBadge
        tone={riskTone}
        icon={approval.risk === "high" ? "warn-tri" : "circle"}
        label={approval.risk}
        size="sm"
        filled
      />
      <DigestText value={approval.id} length={12} prefix={false} />
      <span className={visual.caption}>{approval.created_at.slice(11, 16)}</span>
    </div>
  );
}
