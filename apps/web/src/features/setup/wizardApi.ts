/**
 * Wizard 流程可测逻辑（WP-B2）：discovery 降级与 probe 决策抽成纯函数，
 * 供单元测试覆盖（无 React 渲染器依赖）。
 */

import { api } from "../../api/client";
import type { ProbeResultDto } from "../../api/types";

export interface DiscoverOutcome {
  ids: string[];
  error: string | null;
}

export async function discoverOrFallback(endpointId: string): Promise<DiscoverOutcome> {
  try {
    const result = await api.discoverModels(endpointId);
    if (result.model_ids.length === 0) {
      return { ids: [], error: "discovery returned no models — enter a model id manually" };
    }
    return { ids: result.model_ids, error: null };
  } catch (err) {
    return {
      ids: [],
      error: `discovery unavailable — enter a model id manually (${
        err instanceof Error ? err.message : "relay error"
      })`,
    };
  }
}

export type ProbeOutcome = { kind: "no-models" } | { kind: "result"; result: ProbeResultDto };

export async function probeFirstModel(endpointId: string): Promise<ProbeOutcome> {
  const models = await api.listModels(endpointId);
  if (models.length === 0) {
    return { kind: "no-models" };
  }
  const result = await api.probeModel(models[0]?.id ?? "");
  return { kind: "result", result };
}
