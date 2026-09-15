/** 项目注册表客户端（PLAN-041 WP-A；DELETE 语义见 PLAN-061：引用不可删）。 */

import { newIdempotencyKey, request } from "./http";
import type { ProjectCreateDto, ProjectDto, ProjectUpdateDto } from "./types";

export const projectsClient = {
  list(): Promise<ProjectDto[]> {
    return request("/projects", { method: "GET" });
  },
  create(payload: ProjectCreateDto): Promise<ProjectDto> {
    return request("/projects", { method: "POST", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() });
  },
  update(projectId: string, payload: ProjectUpdateDto): Promise<ProjectDto> {
    return request(
      `/projects/${encodeURIComponent(projectId)}`,
      { method: "PATCH", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  /** 204 无响应体；仍有研究数据引用时后端 409（detail 直接呈现，不静默级联）。 */
  remove(projectId: string): Promise<void> {
    return request(
      `/projects/${encodeURIComponent(projectId)}`,
      { method: "DELETE" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
};
