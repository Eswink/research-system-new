/** 运维观测客户端（遥测/成本/趋势/集群/放置，只读）。 */

import type {
  ClusterViewDto,
  CostViewDto,
  RunPlacementDto,
  RunTelemetryDto,
  TrendViewDto,
} from "./types";
import { request } from "./http";

export const operationsClient = {
  telemetry(runId: string): Promise<RunTelemetryDto> {
    return request(`/runs/${encodeURIComponent(runId)}/telemetry`, { method: "GET" });
  },
  cost(runId: string): Promise<CostViewDto> {
    return request(`/runs/${encodeURIComponent(runId)}/cost`, { method: "GET" });
  },
  trend(
    datasetId?: string,
    expectedDigests: string[] = [],
    limit?: number,
  ): Promise<TrendViewDto> {
    const params = new URLSearchParams();
    if (datasetId !== undefined && datasetId !== "") {
      params.set("dataset_id", datasetId);
    }
    for (const digest of expectedDigests) {
      params.append("expected_digests", digest);
    }
    if (limit !== undefined) {
      params.set("limit", String(limit));
    }
    const suffix = params.size > 0 ? `?${params.toString()}` : "";
    return request(`/evaluations/trend${suffix}`, { method: "GET" });
  },
  clusterWorkers(): Promise<ClusterViewDto> {
    return request("/cluster/workers", { method: "GET" });
  },
  placement(runId: string): Promise<RunPlacementDto> {
    return request(`/runs/${encodeURIComponent(runId)}/placement`, { method: "GET" });
  },
};
