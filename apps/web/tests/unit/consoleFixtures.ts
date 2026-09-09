import type { BudgetViewDto, ClaimMapDto, EvidenceDto, RunEventDto, UsageEntryDto } from
  "../../src/api/types";

export const usageEntry: UsageEntryDto = {
  entry_id: "entry-one", resource_type: "MODEL_TOKENS", quantity: 0, unit: "tokens",
  quantity_status: "UNKNOWN", unavailable_reason: "provider omitted usage",
  cost_status: "UNKNOWN", estimated_cost_minor: null, actual_cost_minor: null,
  currency: "JPY", attempt: 1, run_id: "run-one", model_id: null, task_id: null,
};

export const usageView: BudgetViewDto = {
  entries: [usageEntry], total_estimated_cost_minor: null, total_currency: "JPY",
  known_cost_subtotal_minor: 125, unknown_cost_entries: 1, reservations: [],
};

export const claimsView: ClaimMapDto = {
  degraded: false, unsupported_claims: [], contradictory_claims: [],
  claims: [{ id: "claim-one", statement: "Example statement", status: "PROPOSED", author: null,
    relations: [{ claim_id: "claim-one", evidence_id: "evidence-one",
      relation: "SUPPORTS", strength: 0.4 }] }],
};

export const evidenceRecord: EvidenceDto = {
  id: "evidence-one", source_ref: "source-one", content_digest: "sha256:content",
  run_id: "run-one", experiment_run_id: null, artifact_id: "artifact-one",
  image_digest: null, environment_digest: null, model_refs: [], manifest_digest: null,
};

export const eventFrame: RunEventDto = {
  event_id: "event-one", type: "task.completed", schema_version: "0.4.0",
  occurred_at: "2026-09-09T00:00:00Z", actor: "system", scope: "project",
  run_id: "run-one", task_id: null, trace_id: null, payload: {},
};
