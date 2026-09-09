import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ApprovalCard.module.css";

interface ApprovalCardSection2Props {
  approval: FixtureTypes.Approval;
}

export function ApprovalCardSection2({ approval }: ApprovalCardSection2Props) {
  return (
    <div className={visual.label2}>
      {approval.action.target && (
        <>
          target: <span className="mono">{approval.action.target}</span>
        </>
      )}
      {approval.action.delta_minor && (
        <> · Δ ${(approval.action.delta_minor / 100000).toFixed(2)}</>
      )}
      {approval.action.from && (
        <>
          {" "}
          · <span className="mono">{approval.action.from}</span> →{" "}
          <span className="mono">{approval.action.to}</span>
        </>
      )}
    </div>
  );
}
