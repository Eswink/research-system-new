/** Ops 只读运维投影客户端（PLAN-20260914-045 WP-C）。 */

import { getActiveProjectId } from "./activeProject";
import { request } from "./http";
import type {
  AlertsViewDto,
  DataHealthViewDto,
  IncidentsViewDto,
  SchedulesViewDto,
} from "./types";

export const opsViewClient = {
  alerts(): Promise<AlertsViewDto> {
    const projectId = getActiveProjectId();
    return request(`/projects/${encodeURIComponent(projectId)}/ops/alerts`, { method: "GET" });
  },
  incidents(): Promise<IncidentsViewDto> {
    const projectId = getActiveProjectId();
    return request(`/projects/${encodeURIComponent(projectId)}/ops/incidents`, { method: "GET" });
  },
  schedules(): Promise<SchedulesViewDto> {
    return request("/ops/schedules", { method: "GET" });
  },
  dataHealth(): Promise<DataHealthViewDto> {
    const projectId = getActiveProjectId();
    return request(`/projects/${encodeURIComponent(projectId)}/ops/data-health`, {
      method: "GET",
    });
  },
};
