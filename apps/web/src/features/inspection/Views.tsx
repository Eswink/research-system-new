import type { BudgetViewDto, ClaimMapDto } from "../../api/types";

const costStatusLabel = (status: string): string => {
  if (status === "UNKNOWN") {
    return "unknown（not 0）";
  }
  return "known";
};

export function ClaimMapView({ claims }: { claims: ClaimMapDto }) {
  return (
    <div data-testid="claim-map">
      <h3>Claims & Evidence</h3>
      {claims.contradictory_claims.length > 0 && (
        <p className="warning" data-testid="contradiction-warning">
          Contradiction: {claims.contradictory_claims.join(", ")}
        </p>
      )}
      {claims.unsupported_claims.length > 0 && (
        <p className="warning" data-testid="unsupported-warning">
          Unsupported claims: {claims.unsupported_claims.join(", ")}
        </p>
      )}
      <ul>
        {claims.claims.map((claim) => (
          <li key={claim.id}>
            <strong>{claim.statement}</strong> · status: {claim.status}
            <ul>
              {claim.relations.map((relation, index) => (
                <li key={`${relation.evidence_id}-${String(index)}`}>
                  [{relation.relation}] {relation.evidence_id}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function UsageView({ usage }: { usage: BudgetViewDto }) {
  return (
    <div data-testid="usage-view">
      <h3>Budget & Usage</h3>
      <p>
        Total estimated cost: {String(usage.total_estimated_cost_minor / 100)} USD ·
        unknown entries: {String(usage.unknown_cost_entries)}（unknown ≠ 0）
      </p>
      <ul>
        {usage.entries.map((entry) => (
          <li key={entry.entry_id}>
            {entry.resource_type} · {String(entry.quantity)} {entry.unit} ·{" "}
            {costStatusLabel(entry.cost_status)}
          </li>
        ))}
      </ul>
    </div>
  );
}