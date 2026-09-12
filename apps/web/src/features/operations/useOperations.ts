import { api } from "../../api/client";
import type { CostViewDto, RunTelemetryDto, TrendViewDto } from "../../api/types";

export interface OperationsRunSnapshot {
  telemetry: RunTelemetryDto;
  cost: CostViewDto;
}

/** 一次 run 的 telemetry + cost 联合读取（Promise.all，任一失败即整体失败）。 */
export function fetchOperationsRun(runId: string): Promise<OperationsRunSnapshot> {
  return Promise.all([api.runTelemetry(runId), api.runCost(runId)]).then(([telemetry, cost]) => ({
    telemetry,
    cost,
  }));
}

/** 评测趋势读取（dataset / expected digests / limit 透传）。 */
export function fetchOperationsTrend(
  datasetId?: string,
  expectedDigests: string[] = [],
  limit?: number,
): Promise<TrendViewDto> {
  return api.evaluationsTrend(datasetId, expectedDigests, limit);
}

export function operationsErrorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "operations failed";
}
