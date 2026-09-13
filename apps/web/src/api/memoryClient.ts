/** 产品 Memory 控制面客户端（WP-F；PG canonical state，SQLite 503 诚实呈现）。 */

import { getActiveProjectId } from "./activeProject";
import { newIdempotencyKey, request } from "./http";
import type {
  MemoryCommittedDto,
  MemoryProposalCreateDto,
  MemoryViewDto,
} from "./types";

export const memoryClient = {
  list(projectId = getActiveProjectId()): Promise<MemoryViewDto> {
    return request(`/projects/${encodeURIComponent(projectId)}/memory`, { method: "GET" });
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
