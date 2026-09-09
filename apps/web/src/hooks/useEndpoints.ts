import { api } from "../api/client";
import type { LlmEndpointReadDto } from "../api/types";
import { useResource } from "./useResource";

export interface EndpointsState {
  endpoints: LlmEndpointReadDto[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

/** 端点列表 server-state cache；刷新后从 API 恢复，不写 localStorage */
export function useEndpoints(enabled = true): EndpointsState {
  const resource = useResource(enabled ? "llm-endpoints" : null, () => api.listEndpoints());
  return {
    endpoints: resource.data ?? [],
    loading: enabled && (resource.phase === "idle" || resource.phase === "loading"),
    error: enabled ? resource.error : null,
    refresh: resource.reload,
  };
}
