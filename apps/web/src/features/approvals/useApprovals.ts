import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import { ApiError } from "../../api/http";
import type { ApprovalDto } from "../../api/types";
import { useResource } from "../../hooks/useResource";

/** Read-only pending projection plus explicit, versioned decisions.
 * No optimistic policy changes.
 */
export function useApprovals() {
  const query = useResource("pending-approvals", () => api.listApprovals());
  const [error, setError] = useState<string | null>(null);
  const [decision, setDecision] = useState<ApprovalDto | null>(null);
  const [deciding, setDeciding] = useState(false);
  const active = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const decide = async (approval: ApprovalDto, action: "approve" | "deny") => {
    if (active.current || query.phase !== "ready") return;
    active.current = true;
    setDeciding(true);
    setError(null);
    setDecision(null);
    try {
      const result = await api.decideApproval(approval.id, action, approval.version);
      if (mounted.current) {
        setDecision(result);
        query.reload();
      }
    } catch (cause) {
      if (mounted.current) {
        setError(cause instanceof Error ? cause.message : "Approval decision failed");
        if (cause instanceof ApiError && (cause.status === 412 || cause.status === 409))
          query.reload();
      }
    } finally {
      active.current = false;
      if (mounted.current) setDeciding(false);
    }
  };
  return { query, error, decision, deciding, decide };
}
