/** Ops 写面客户端（G7 / PLAN-20260915-059）：告警规则 CRUD + 事故处置。
 *
 * 约束与主 client 一致：只消费 types.ts DTO；mutating 带 Idempotency-Key；
 * 写面的效果由只读读面（alerts 的 muted/incident_id、incidents 的已登记列表）呈现。
 */

import { getActiveProjectId } from "./activeProject";
import { newIdempotencyKey, request } from "./http";
import type {
  AlertRuleDto,
  AlertRulePatchDto,
  AlertRuleWriteDto,
  AlertRulesViewDto,
  IncidentAssignDto,
  IncidentCloseDto,
  IncidentDeclareDto,
  IncidentItemDto,
} from "./types";

export const opsControlClient = {
  rules(): Promise<AlertRulesViewDto> {
    const projectId = getActiveProjectId();
    return request(`/projects/${encodeURIComponent(projectId)}/ops/alert-rules`, {
      method: "GET",
    });
  },
  createRule(payload: AlertRuleWriteDto): Promise<AlertRuleDto> {
    const projectId = getActiveProjectId();
    return request(`/projects/${encodeURIComponent(projectId)}/ops/alert-rules`, {
      method: "POST",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey() });
  },
  patchRule(ruleId: string, payload: AlertRulePatchDto): Promise<AlertRuleDto> {
    return request(`/ops/alert-rules/${encodeURIComponent(ruleId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey() });
  },
  deleteRule(ruleId: string): Promise<void> {
    return request(`/ops/alert-rules/${encodeURIComponent(ruleId)}`, { method: "DELETE" }, {
      idempotencyKey: newIdempotencyKey(),
    });
  },
  declareIncident(payload: IncidentDeclareDto): Promise<IncidentItemDto> {
    const projectId = getActiveProjectId();
    return request(`/projects/${encodeURIComponent(projectId)}/ops/incidents`, {
      method: "POST",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey() });
  },
  assignIncident(incidentId: string, payload: IncidentAssignDto): Promise<IncidentItemDto> {
    return request(`/ops/incidents/${encodeURIComponent(incidentId)}/assign`, {
      method: "POST",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey() });
  },
  closeIncident(incidentId: string, payload: IncidentCloseDto): Promise<IncidentItemDto> {
    return request(`/ops/incidents/${encodeURIComponent(incidentId)}/close`, {
      method: "POST",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey() });
  },
};
