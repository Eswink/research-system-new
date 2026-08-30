import { useState } from "react";

import { api } from "../../api/client";
import type { CostViewDto, RunTelemetryDto, TrendViewDto } from "../../api/types";

export interface OperationsState {
  telemetry: RunTelemetryDto | null;
  cost: CostViewDto | null;
  trend: TrendViewDto | null;
  error: string | null;
  busy: boolean;
  loadRun: (runId: string) => Promise<void>;
  loadTrend: (
    datasetId?: string,
    expectedDigests?: string[],
    limit?: number,
  ) => Promise<void>;
}

export interface OperationsRunSnapshot {
  telemetry: RunTelemetryDto;
  cost: CostViewDto;
}

/** 一次 run 的 telemetry + cost 联合读取（Promise.all，任一失败即整体失败）。 */
export function fetchOperationsRun(runId: string): Promise<OperationsRunSnapshot> {
  return Promise.all([api.runTelemetry(runId), api.runCost(runId)]).then(
    ([telemetry, cost]) => ({ telemetry, cost }),
  );
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

/** Operations 状态（server-state cache；只 render 投影，无本地 truth） */
export function useOperations(): OperationsState {
  const [telemetry, setTelemetry] = useState<RunTelemetryDto | null>(null);
  const [cost, setCost] = useState<CostViewDto | null>(null);
  const [trend, setTrend] = useState<TrendViewDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadRun = async (runId: string) => {
    setBusy(true);
    setError(null);
    try {
      const snapshot = await fetchOperationsRun(runId);
      setTelemetry(snapshot.telemetry);
      setCost(snapshot.cost);
    } catch (err) {
      setError(operationsErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const loadTrend = async (
    datasetId?: string,
    expectedDigests: string[] = [],
    limit?: number,
  ) => {
    setBusy(true);
    setError(null);
    try {
      setTrend(await fetchOperationsTrend(datasetId, expectedDigests, limit));
    } catch (err) {
      setError(operationsErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return { telemetry, cost, trend, error, busy, loadRun, loadTrend };
}
