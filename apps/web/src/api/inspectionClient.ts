/** 证据/论断/用量/导出客户端（只读投影）。 */

import { request } from "./http";
import type {
  BudgetViewDto,
  ClaimMapDto,
  DeliverableDto,
  EvidenceDto,
  ExperimentViewDto,
  ExportBundleDto,
  LineageDto,
} from "./types";

export const inspectionClient = {
  evidence(runId: string): Promise<EvidenceDto[]> {
    return request(`/runs/${encodeURIComponent(runId)}/evidence`, { method: "GET" });
  },
  claimMap(runId: string): Promise<ClaimMapDto> {
    return request(`/runs/${encodeURIComponent(runId)}/claims`, { method: "GET" });
  },
  usage(runId: string): Promise<BudgetViewDto> {
    return request(`/runs/${encodeURIComponent(runId)}/usage`, { method: "GET" });
  },
  experiments(runId: string): Promise<ExperimentViewDto> {
    return request(`/runs/${encodeURIComponent(runId)}/experiments`, { method: "GET" });
  },
  export(runId: string): Promise<ExportBundleDto> {
    return request(`/runs/${encodeURIComponent(runId)}/export`, { method: "GET" });
  },
  deliverable(runId: string): Promise<DeliverableDto> {
    return request(`/runs/${encodeURIComponent(runId)}/deliverable`, { method: "GET" });
  },
  lineage(runId: string): Promise<LineageDto> {
    return request(`/runs/${encodeURIComponent(runId)}/lineage`, { method: "GET" });
  },
};
