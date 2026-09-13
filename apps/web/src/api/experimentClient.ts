/** 实验平面客户端（WP-E）：项目级 run 视图 + 计划预注册/归档。 */

import { getActiveProjectId } from "./activeProject";
import { newIdempotencyKey, request } from "./http";
import type {
  ExperimentPlanCreateDto,
  ExperimentPlanDto,
  ProjectExperimentsViewDto,
} from "./types";

export const experimentClient = {
  listForProject(projectId = getActiveProjectId()): Promise<ProjectExperimentsViewDto> {
    return request(`/projects/${encodeURIComponent(projectId)}/experiments`, { method: "GET" });
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
};
