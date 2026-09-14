/** 库目录客户端（PLAN-20260914-044 WP-C）：prompts/datasets/notebooks 共享。 */

import { getActiveProjectId } from "./activeProject";
import { newIdempotencyKey, request } from "./http";
import type { LibraryResourceDto, ResourceKind } from "./types";

export const libraryClient = {
  list(kind: ResourceKind): Promise<LibraryResourceDto[]> {
    const projectId = getActiveProjectId();
    return request(
      `/projects/${encodeURIComponent(projectId)}/library?kind=${encodeURIComponent(kind)}`,
      { method: "GET" },
    );
  },
  create(payload: {
    kind: ResourceKind;
    name: string;
    description?: string;
    content_ref?: string | null;
    tags?: string[];
  }): Promise<LibraryResourceDto> {
    const projectId = getActiveProjectId();
    return request(
      `/projects/${encodeURIComponent(projectId)}/library`,
      { method: "POST", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  update(
    resourceId: string,
    payload: { name?: string; status?: "ACTIVE" | "ARCHIVED" },
  ): Promise<LibraryResourceDto> {
    return request(
      `/library/${encodeURIComponent(resourceId)}`,
      { method: "PATCH", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
};
