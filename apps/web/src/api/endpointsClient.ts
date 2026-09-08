/** 中转站（LLM endpoint）客户端。 */

import type {
  DiscoverModelsResultDto,
  EndpointHealthDto,
  EndpointTestResultDto,
  LlmEndpointCreateDto,
  LlmEndpointReadDto,
  LlmEndpointUpdateDto,
  Version,
} from "./types";
import { newIdempotencyKey, request, requestWithEtag, type ResponseWithEtag } from "./http";

export const endpointsClient = {
  list(): Promise<LlmEndpointReadDto[]> {
    return request("/llm-endpoints", { method: "GET" });
  },
  create(payload: LlmEndpointCreateDto): Promise<ResponseWithEtag<LlmEndpointReadDto>> {
    return requestWithEtag("/llm-endpoints", {
      method: "POST",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey() });
  },
  get(id: string): Promise<ResponseWithEtag<LlmEndpointReadDto>> {
    return requestWithEtag(`/llm-endpoints/${encodeURIComponent(id)}`, { method: "GET" });
  },
  update(
    id: string,
    payload: LlmEndpointUpdateDto,
    ifMatch: Version,
  ): Promise<ResponseWithEtag<LlmEndpointReadDto>> {
    return requestWithEtag(`/llm-endpoints/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey(), ifMatch });
  },
  test(endpointId: string, modelId: string): Promise<EndpointTestResultDto> {
    return request(`/llm-endpoints/${encodeURIComponent(endpointId)}/test`, {
      method: "POST",
      body: JSON.stringify({ model_id: modelId }),
    });
  },
  discoverModels(endpointId: string): Promise<DiscoverModelsResultDto> {
    return request(`/llm-endpoints/${encodeURIComponent(endpointId)}/discover-models`, {
      method: "POST",
    });
  },
  health(endpointId: string): Promise<EndpointHealthDto> {
    return request(`/llm-endpoints/${encodeURIComponent(endpointId)}/health`, { method: "GET" });
  },
};
