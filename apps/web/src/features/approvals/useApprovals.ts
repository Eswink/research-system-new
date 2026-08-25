import { useState } from "react";

import { api } from "../../api/client";
import type { ApprovalDto } from "../../api/types";

const handleError = (err: unknown): string => {
  return err instanceof Error ? err.message : "approval operation failed";
};

export interface ApprovalFlow {
  approvals: ApprovalDto[];
  error: string | null;
  refresh: () => Promise<void>;
  decide: (approval: ApprovalDto, decision: "approve" | "deny") => Promise<void>;
}

/** 审批状态（事件投影；刷新后从 API 恢复，不持 Canonical State） */
export function useApprovals(): ApprovalFlow {
  const [approvals, setApprovals] = useState<ApprovalDto[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      const items = await api.listApprovals();
      setApprovals(items);
    } catch (err) {
      setError(handleError(err));
    }
  };

  const decide = async (approval: ApprovalDto, decision: "approve" | "deny") => {
    setError(null);
    try {
      await api.decideApproval(approval.id, decision, approval.version);
      await refresh();
    } catch (err) {
      setError(handleError(err));
    }
  };

  return { approvals, error, refresh, decide };
}