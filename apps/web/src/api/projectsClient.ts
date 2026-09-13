/** 项目注册表客户端（PLAN-041 WP-A；无 DELETE：归档即终态）。 */

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
};
