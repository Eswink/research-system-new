/** 证据/论断/用量/导出客户端（只读投影）。 */

import { getActiveProjectId } from "./activeProject";
import { request } from "./http";
import type {
  BudgetViewDto,
  ClaimMapDto,
  CostForecastDto,
  DeliverableDto,
  EvidenceDto,
  ExperimentViewDto,
  ExportBundleDto,
  LineageDto,
  ProjectLineageDto,
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
  costForecast(runId: string): Promise<CostForecastDto> {
    return request(`/runs/${encodeURIComponent(runId)}/cost-forecast`, { method: "GET" });
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
  projectLineage(projectId: string = getActiveProjectId()): Promise<ProjectLineageDto> {
    return request(`/projects/${encodeURIComponent(projectId)}/lineage`, { method: "GET" });
  },
};
