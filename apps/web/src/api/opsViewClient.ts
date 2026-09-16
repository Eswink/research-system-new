/** Ops 只读运维投影客户端（PLAN-20260914-045 WP-C）+ 调度定义写面（EC-03）。
 *
 * 约束与主 client 一致：只消费 types.ts DTO；mutating 带 Idempotency-Key。
 */

import { getActiveProjectId } from "./activeProject";
import { newIdempotencyKey, request } from "./http";
import type {
  AlertsViewDto,
  DataHealthViewDto,
  IncidentsViewDto,
  ScheduleCreateDto,
  ScheduleEntryDto,
  SchedulesViewDto,
  ScheduleUpdateDto,
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
  createSchedule(payload: ScheduleCreateDto): Promise<ScheduleEntryDto> {
    return request(
      "/ops/schedules",
      { method: "POST", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  updateSchedule(name: string, payload: ScheduleUpdateDto): Promise<ScheduleEntryDto> {
    return request(
      `/ops/schedules/${encodeURIComponent(name)}`,
      { method: "PATCH", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  triggerSchedule(name: string): Promise<ScheduleEntryDto> {
    return request(
      `/ops/schedules/${encodeURIComponent(name)}/trigger`,
      { method: "POST" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  dataHealth(): Promise<DataHealthViewDto> {
    const projectId = getActiveProjectId();
    return request(`/projects/${encodeURIComponent(projectId)}/ops/data-health`, {
      method: "GET",
    });
  },
};
