/** 实验平面客户端（WP-E）：项目级 run 视图 + 计划预注册/归档 + G14 队列。 */

import { getActiveProjectId } from "./activeProject";
import { newIdempotencyKey, request } from "./http";
import type {
  ExperimentPlanCreateDto,
  ExperimentPlanDto,
  ExperimentQueueEnqueueDto,
  ExperimentQueueEntryDto,
  ExperimentQueueViewDto,
  ProjectExperimentsViewDto,
} from "./types";

export const experimentClient = {
  listForProject(projectId = getActiveProjectId()): Promise<ProjectExperimentsViewDto> {
    return request(`/projects/${encodeURIComponent(projectId)}/experiments`, { method: "GET" });
  },
  listPlans(state?: string): Promise<ExperimentPlanDto[]> {
    const query = state === undefined ? "" : `?state=${encodeURIComponent(state)}`;
    return request(`/experiment-plans${query}`, { method: "GET" });
  },
  createPlan(payload: ExperimentPlanCreateDto): Promise<ExperimentPlanDto> {
    return request(
      `/projects/${encodeURIComponent(getActiveProjectId())}/experiments`,
      { method: "POST", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  archivePlan(planId: string): Promise<ExperimentPlanDto> {
    return request(
      `/experiments/${encodeURIComponent(planId)}/archive`,
      { method: "POST" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  listQueue(projectId = getActiveProjectId()): Promise<ExperimentQueueViewDto> {
    return request(`/projects/${encodeURIComponent(projectId)}/experiment-queue`, {
      method: "GET",
    });
  },
  enqueue(
    planId: string,
    payload: ExperimentQueueEnqueueDto,
    projectId = getActiveProjectId(),
  ): Promise<ExperimentQueueEntryDto> {
    return request(
      `/projects/${encodeURIComponent(projectId)}/experiments/${encodeURIComponent(planId)}/queue`,
      { method: "POST", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  reschedule(entryId: string, notBefore: string | null): Promise<ExperimentQueueEntryDto> {
    return request(
      `/experiment-queue/${encodeURIComponent(entryId)}`,
      { method: "PATCH", body: JSON.stringify({ not_before: notBefore }) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  cancel(entryId: string): Promise<ExperimentQueueEntryDto> {
    return request(
      `/experiment-queue/${encodeURIComponent(entryId)}`,
      { method: "DELETE" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
};
