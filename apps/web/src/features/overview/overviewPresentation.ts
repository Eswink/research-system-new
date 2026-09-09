import type { BudgetViewDto, ClaimMapDto, TaskDto } from "../../api/types";

export function taskProgress(tasks: readonly TaskDto[] | null) {
  if (tasks === null) return null;
  const done = tasks.filter((task) => task.status === "SUCCEEDED").length;
  return { done, total: tasks.length, ratio: tasks.length === 0 ? undefined : done / tasks.length };
}

export function claimSummary(claims: ClaimMapDto | null) {
  if (claims === null) return null;
  return {
    total: claims.claims.length,
    unsupported: claims.unsupported_claims.length,
    disputed: claims.contradictory_claims.length,
    degraded: claims.degraded,
  };
}

/** Use the API's aggregate, not a browser re-sum or the known subtotal as a total. */
export function usageSummary(usage: BudgetViewDto | null) {
  if (usage === null) return null;
  return {
    total: usage.total_estimated_cost_minor,
    currency: usage.total_currency,
    knownSubtotal: usage.known_cost_subtotal_minor,
    unknownEntries: usage.unknown_cost_entries,
  };
}
