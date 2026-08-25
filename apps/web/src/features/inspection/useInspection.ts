import { useState } from "react";

import { api } from "../../api/client";
import type { BudgetViewDto, ClaimMapDto } from "../../api/types";

const handleError = (err: unknown): string => {
  return err instanceof Error ? err.message : "inspection failed";
};

export interface InspectionState {
  claims: ClaimMapDto | null;
  usage: BudgetViewDto | null;
  error: string | null;
  busy: boolean;
  load: (runId: string) => Promise<void>;
}

/** Inspection 状态（server-state cache；只 render persisted truth） */
export function useInspection(): InspectionState {
  const [claims, setClaims] = useState<ClaimMapDto | null>(null);
  const [usage, setUsage] = useState<BudgetViewDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = async (runId: string) => {
    setBusy(true);
    setError(null);
    try {
      const [claimMap, budget] = await Promise.all([
        api.runClaimMap(runId),
        api.runUsage(runId),
      ]);
      setClaims(claimMap);
      setUsage(budget);
    } catch (err) {
      setError(handleError(err));
    } finally {
      setBusy(false);
    }
  };

  return { claims, usage, error, busy, load };
}