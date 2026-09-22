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
  // 来源记录读面（GOAL-010 EC-02）：自产 evidence 的 origin 就是它自己的 source_ref，
  // 信任标签 GENERATED——与后端 register_source 的取值同形。
  source_origin: "source-one", source_trust_label: "GENERATED",
  source_access_time: "2026-09-09T00:00:00Z",
  // 工具观测读面（GOAL-011 EC-01）：这条是自产 evidence、不是工具来源
  // ⇒ 空数组，与后端 `Evidence.tool_refs` 的默认值同形。
  tool_refs: [],
};

export const eventFrame: RunEventDto = {
  event_id: "event-one", type: "task.completed", schema_version: "0.4.0",
  occurred_at: "2026-09-09T00:00:00Z", actor: "system", scope: "project",
  run_id: "run-one", task_id: null, trace_id: null, payload: {},
};
