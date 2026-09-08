/** 模型目录客户端。 */

import type {
  CompatibilityViewDto,
  ModelCreateDto,
  ModelReadDto,
  ModelUpdateDto,
  ProbeResultDto,
  Version,
} from "./types";
import { newIdempotencyKey, request, requestWithEtag, type ResponseWithEtag } from "./http";

export const modelsClient = {
  list(endpointId?: string): Promise<ModelReadDto[]> {
    const query = endpointId ? `?endpoint_id=${encodeURIComponent(endpointId)}` : "";
    return request(`/models${query}`, { method: "GET" });
  },
  create(payload: ModelCreateDto): Promise<ResponseWithEtag<ModelReadDto>> {
    return requestWithEtag("/models", {
      method: "POST",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey() });
  },
  get(id: string): Promise<ModelReadDto> {
    return request(`/models/${encodeURIComponent(id)}`, { method: "GET" });
  },
  update(id: string, payload: ModelUpdateDto, ifMatch: Version): Promise<ModelReadDto> {
    return request(`/models/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey(), ifMatch });
  },
  probe(id: string): Promise<ProbeResultDto> {
    return request(`/models/${encodeURIComponent(id)}/probe`, { method: "POST" });
  },
  compatibility(modelId: string): Promise<CompatibilityViewDto> {
    return request(`/models/${encodeURIComponent(modelId)}/compatibility`, { method: "GET" });
  },
};
