/** 产品 Memory 控制面客户端（WP-F；PG canonical state，SQLite 503 诚实呈现）。 */

import { getActiveProjectId } from "./activeProject";
import { newIdempotencyKey, request } from "./http";
import type {
  MemoryCommittedDto,
  MemoryProposalCreateDto,
  MemoryValidityViewDto,
  MemoryViewDto,
} from "./types";

export const memoryClient = {
  list(projectId = getActiveProjectId()): Promise<MemoryViewDto> {
    return request(`/projects/${encodeURIComponent(projectId)}/memory`, { method: "GET" });
  },
  /**
   * 按**显式时点**读时效（GOAL-20261103-104 EC-03；服务端能力，前端暂不暴露）。
   *
   * `at` 由调用方给 ⇒ 同一份数据同一时点判定必相同（服务端不读挂钟）。登记在
   * `docs/frontend/UNCONSUMED.md`：记忆面目前只展示列表，时效视图没有 UI 需求。
   */
  validity(
    at: string,
    projectId = getActiveProjectId(),
  ): Promise<MemoryValidityViewDto> {
    return request(
      `/projects/${encodeURIComponent(projectId)}/memory/validity?at=${encodeURIComponent(at)}`,
      { method: "GET" },
    );
  },
  propose(payload: MemoryProposalCreateDto): Promise<MemoryCommittedDto> {
    return request(
      "/memory/proposals",
      { method: "POST", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  remove(memoryId: string): Promise<void> {
    return request(
      `/memory/${encodeURIComponent(memoryId)}`,
      { method: "DELETE" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
};
