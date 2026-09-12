/** 中转站（LLM endpoint）客户端。 */

import { newIdempotencyKey, request, requestWithEtag, type ResponseWithEtag } from "./http";
import type {
  DiscoverModelsResultDto,
  EndpointHealthDto,
  EndpointTestRequestDto,
  EndpointTestResultDto,
  LlmEndpointCreateDto,
  LlmEndpointReadDto,
  LlmEndpointUpdateDto,
  Version,
} from "./types";

export const endpointsClient = {
  list(): Promise<LlmEndpointReadDto[]> {
    return request("/llm-endpoints", { method: "GET" });
  },
  create(payload: LlmEndpointCreateDto): Promise<ResponseWithEtag<LlmEndpointReadDto>> {
    return requestWithEtag(
      "/llm-endpoints",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  get(id: string): Promise<ResponseWithEtag<LlmEndpointReadDto>> {
    return requestWithEtag(`/llm-endpoints/${encodeURIComponent(id)}`, { method: "GET" });
  },
  update(
    id: string,
    payload: LlmEndpointUpdateDto,
    ifMatch: Version,
  ): Promise<ResponseWithEtag<LlmEndpointReadDto>> {
    return requestWithEtag(
      `/llm-endpoints/${encodeURIComponent(id)}`,
      {
        method: "PATCH",
        body: JSON.stringify(payload),
      },
      { idempotencyKey: newIdempotencyKey(), ifMatch },
    );
  },
  test(endpointId: string, modelId: string): Promise<EndpointTestResultDto> {
    const payload: EndpointTestRequestDto = { model_id: modelId };
    return request(`/llm-endpoints/${encodeURIComponent(endpointId)}/test`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  /** 删除用户 relay（WP-B G10）：被用户 model 引用 → 409。 */
  remove(endpointId: string): Promise<void> {
    return request(
      `/llm-endpoints/${encodeURIComponent(endpointId)}`,
      { method: "DELETE" },
      { idempotencyKey: newIdempotencyKey() },
    );
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
