import type { ApprovalDto } from "../../api/types";
import { useApprovals } from "./useApprovals";

const riskLabel = (risk: string): string => {
  if (risk === "HIGH") {
    return "high risk";
  }
  if (risk === "CRITICAL") {
    return "critical";
  }
  return risk.toLowerCase();
};

export function ApprovalListItem({
  approval,
  onDecide,
}: {
  approval: ApprovalDto;
  onDecide: (approval: ApprovalDto, decision: "approve" | "deny") => void;
}) {
  return (
    <li key={approval.id}>
      <strong>{approval.action}</strong> · {riskLabel(approval.risk)} · {approval.context}
      <span className="policy-source">({approval.policy_source})</span>
      <button
        type="button"
        onClick={() => {
          onDecide(approval, "approve");
        }}
        data-testid="approve-button"
      >
        Approve
      </button>
      <button
        type="button"
        onClick={() => {
          if (window.confirm(`Deny approval for ${approval.action}? The run will be rejected.`)) {
            onDecide(approval, "deny");
          }
        }}
        data-testid="deny-button"
      >
        Deny
      </button>
    </li>
  );
}

/**
 * 审批面板：展示待决审批（事件投影），Approve/Deny 走后端裁决。
 * UI 不决定 Policy（hidden button != authorization）：即使直接调 API，
 * 后端仍执行状态机 + If-Match 校验；stale version → 412 → 刷新列表。
 */
export function ApprovalsPanel() {
  const flow = useApprovals();

  const submitDecide = (approval: ApprovalDto, decision: "approve" | "deny") => {
    flow.decide(approval, decision).then(() => undefined, () => undefined);
  };

  const load = () => {
    flow.refresh().then(() => undefined, () => undefined);
  };

  return (
    <section className="approvals" data-testid="approvals-panel">
      <h2>Pending Approvals</h2>
      <button type="button" onClick={load}>
        Refresh
      </button>
      {flow.error !== null && (
        <p className="error" role="alert">
          {flow.error}
        </p>
      )}
      {flow.approvals.length === 0 ? (
        <p data-testid="approvals-empty">No pending approvals.</p>
      ) : (
        <ul data-testid="approvals-list">
          {flow.approvals.map((approval) => (
            <ApprovalListItem
              key={approval.id}
              approval={approval}
              onDecide={submitDecide}
            />
          ))}
        </ul>
      )}
    </section>
  );
}