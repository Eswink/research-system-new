/** 运行与审批客户端。 */

import type {
  ApprovalDto,
  RunDetailDto,
  RunEventDto,
  TaskDto,
  Version,
} from "./types";
import { newIdempotencyKey, request } from "./http";

const PROJECT = "example-project";

export const runClient = {
  start(source: string | { draft_id: string; draft_revision: number }): Promise<RunDetailDto> {
    const body =
      typeof source === "string"
        ? { protocol_path: source }
        : { draft_id: source.draft_id, draft_revision: source.draft_revision };
    return request(`/projects/${PROJECT}/runs`, {
      method: "POST",
      body: JSON.stringify(body),
    }, { idempotencyKey: newIdempotencyKey() });
  },
  list(projectId = PROJECT): Promise<RunDetailDto[]> {
    return request(`/projects/${encodeURIComponent(projectId)}/runs`, { method: "GET" });
  },
  get(runId: string): Promise<RunDetailDto> {
    return request(`/runs/${encodeURIComponent(runId)}`, { method: "GET" });
  },
  cancel(runId: string): Promise<RunDetailDto> {
    return request(`/runs/${encodeURIComponent(runId)}/cancel`, {
      method: "POST",
    }, { idempotencyKey: newIdempotencyKey() });
  },
  /** pause/resume 仅领域状态迁移（不证明实际暂停/恢复执行）。 */
  pause(runId: string): Promise<RunDetailDto> {
    return request(`/runs/${encodeURIComponent(runId)}/pause`, {
      method: "POST",
    }, { idempotencyKey: newIdempotencyKey() });
  },
  resume(runId: string): Promise<RunDetailDto> {
    return request(`/runs/${encodeURIComponent(runId)}/resume`, {
      method: "POST",
    }, { idempotencyKey: newIdempotencyKey() });
  },
  tasks(runId: string): Promise<TaskDto[]> {
    return request(`/runs/${encodeURIComponent(runId)}/tasks`, { method: "GET" });
  },
  events(runId: string): Promise<RunEventDto[]> {
    return request(`/runs/${encodeURIComponent(runId)}/events`, { method: "GET" });
  },
  listApprovals(): Promise<ApprovalDto[]> {
    return request("/approvals", { method: "GET" });
  },
  decideApproval(
    approvalId: string,
    decision: "approve" | "deny",
    version: Version,
  ): Promise<ApprovalDto> {
    return request(`/approvals/${encodeURIComponent(approvalId)}/decide`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    }, { idempotencyKey: newIdempotencyKey(), ifMatch: version });
  },
};
