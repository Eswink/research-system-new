/**
 * 协议草稿 API 客户端（PLAN-20260908-033）。
 *
 * 从 client.ts 拆出（300 行软限制先例：http.ts）。约束与主 client 一致：
 * - 只消费 src/api/types.ts 的 DTO；
 * - mutating 请求带 Idempotency-Key；save 带If-Match（陈旧修订 → 412）。
 */

import type {
  ProblemDto,
  ProtocolDraftRevisionDto,
  ProtocolDraftSummaryDto,
  ProtocolDraftTemplateDto,
  ProtocolDraftValidateResultDto,
  ProtocolDraftViewDto,
  Version,
} from "./types";
import { API_BASE, ApiError, newIdempotencyKey } from "./http";

async function draftRequest<T>(
  path: string,
  init: RequestInit,
  options?: { idempotencyKey?: string | undefined; ifMatch?: Version | undefined },
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (options?.idempotencyKey !== undefined) {
    headers.set("Idempotency-Key", options.idempotencyKey);
  }
  if (options?.ifMatch !== undefined) {
    headers.set("If-Match", options.ifMatch);
  }
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    let problem: ProblemDto | undefined;
    try {
      problem = (await response.json()) as ProblemDto;
    } catch {
      problem = undefined;
    }
    throw new ApiError(
      response.status,
      problem ?? {
        type: "about:blank",
        title: "Request Failed",
        status: response.status,
        detail: `HTTP ${String(response.status)}`,
        instance: path,
      },
    );
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const draftApi = {
  listTemplates(): Promise<ProtocolDraftTemplateDto[]> {
    return draftRequest("/protocol-templates", { method: "GET" });
  },

  getTemplate(templateId: string): Promise<ProtocolDraftTemplateDto> {
    return draftRequest(`/protocol-templates/${encodeURIComponent(templateId)}`, {
      method: "GET",
    });
  },

  validateYaml(yamlText: string): Promise<ProtocolDraftValidateResultDto> {
    return draftRequest("/protocol-drafts/validate", {
      method: "POST",
      body: JSON.stringify({ yaml_text: yamlText }),
    });
  },

  create(name: string, yamlText: string): Promise<ProtocolDraftViewDto> {
    return draftRequest("/projects/example-project/protocol-drafts", {
      method: "POST",
      body: JSON.stringify({ name, yaml_text: yamlText }),
    }, { idempotencyKey: newIdempotencyKey() });
  },

  list(): Promise<ProtocolDraftSummaryDto[]> {
    return draftRequest("/projects/example-project/protocol-drafts", { method: "GET" });
  },

  get(draftId: string): Promise<ProtocolDraftViewDto> {
    return draftRequest(`/protocol-drafts/${encodeURIComponent(draftId)}`, { method: "GET" });
  },

  listRevisions(draftId: string): Promise<ProtocolDraftRevisionDto[]> {
    return draftRequest(`/protocol-drafts/${encodeURIComponent(draftId)}/revisions`, {
      method: "GET",
    });
  },

  getRevision(draftId: string, revision: number): Promise<ProtocolDraftRevisionDto> {
    return draftRequest(
      `/protocol-drafts/${encodeURIComponent(draftId)}/revisions/${String(revision)}`,
      { method: "GET" },
    );
  },

  save(draftId: string, yamlText: string, expectedRevision: number): Promise<ProtocolDraftViewDto> {
    return draftRequest(
      `/protocol-drafts/${encodeURIComponent(draftId)}`,
      {
        method: "PUT",
        body: JSON.stringify({ yaml_text: yamlText, expected_revision: expectedRevision }),
      },
      { idempotencyKey: newIdempotencyKey(), ifMatch: String(expectedRevision) },
    );
  },
};
