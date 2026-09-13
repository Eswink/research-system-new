/**
 * 协议草稿 API 客户端（PLAN-20260908-033；T08 复用统一 http）。
 *
 * 约束与主 client 一致：只消费 types.ts DTO；mutating 带 Idempotency-Key；
 * save 带 If-Match（陈旧修订 → 412）。
 */

import { getActiveProjectId } from "./activeProject";
import { newIdempotencyKey, request } from "./http";
import type {
  ProtocolDraftRevisionDto,
  ProtocolDraftSummaryDto,
  ProtocolDraftTemplateDto,
  ProtocolDraftValidateResultDto,
  ProtocolDraftViewDto,
} from "./types";

export const draftApi = {
  listTemplates(): Promise<ProtocolDraftTemplateDto[]> {
    return request("/protocol-templates", { method: "GET" });
  },

  getTemplate(templateId: string): Promise<ProtocolDraftTemplateDto> {
    return request(`/protocol-templates/${encodeURIComponent(templateId)}`, { method: "GET" });
  },

  validateYaml(yamlText: string): Promise<ProtocolDraftValidateResultDto> {
    return request("/protocol-drafts/validate", {
      method: "POST",
      body: JSON.stringify({ yaml_text: yamlText }),
    });
  },

  create(name: string, yamlText: string): Promise<ProtocolDraftViewDto> {
    return request(
      `/projects/${getActiveProjectId()}/protocol-drafts`,
      {
        method: "POST",
        body: JSON.stringify({ name, yaml_text: yamlText }),
      },
      { idempotencyKey: newIdempotencyKey() },
    );
  },

  list(): Promise<ProtocolDraftSummaryDto[]> {
    return request(`/projects/${getActiveProjectId()}/protocol-drafts`, { method: "GET" });
  },

  get(draftId: string): Promise<ProtocolDraftViewDto> {
    return request(`/protocol-drafts/${encodeURIComponent(draftId)}`, { method: "GET" });
  },

  listRevisions(draftId: string): Promise<ProtocolDraftRevisionDto[]> {
    return request(`/protocol-drafts/${encodeURIComponent(draftId)}/revisions`, { method: "GET" });
  },

  getRevision(draftId: string, revision: number): Promise<ProtocolDraftRevisionDto> {
    return request(
      `/protocol-drafts/${encodeURIComponent(draftId)}/revisions/${String(revision)}`,
      { method: "GET" },
    );
  },

  save(draftId: string, yamlText: string, expectedRevision: number): Promise<ProtocolDraftViewDto> {
    return request(
      `/protocol-drafts/${encodeURIComponent(draftId)}`,
      {
        method: "PUT",
        body: JSON.stringify({ yaml_text: yamlText, expected_revision: expectedRevision }),
      },
      { idempotencyKey: newIdempotencyKey(), ifMatch: String(expectedRevision) },
    );
  },

  /** 物理删除草稿与全部修订（WP-B G10；深链随后 404 是正确态）。 */
  remove(draftId: string): Promise<void> {
    return request(
      `/protocol-drafts/${encodeURIComponent(draftId)}`,
      { method: "DELETE" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
};
