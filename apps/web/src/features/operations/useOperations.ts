import { useState } from "react";

import { api } from "../../api/client";
import type { CostViewDto, RunTelemetryDto, TrendViewDto } from "../../api/types";

const handleError = (err: unknown): string => {
  return err instanceof Error ? err.message : "operations failed";
};

export interface OperationsState {
  telemetry: RunTelemetryDto | null;
  cost: CostViewDto | null;
  trend: TrendViewDto | null;
  error: string | null;
  busy: boolean;
  loadRun: (runId: string) => Promise<void>;
  loadTrend: (datasetId?: string) => Promise<void>;
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
      const [telemetryView, costView] = await Promise.all([
        api.runTelemetry(runId),
        api.runCost(runId),
      ]);
      setTelemetry(telemetryView);
      setCost(costView);
    } catch (err) {
      setError(handleError(err));
    } finally {
      setBusy(false);
    }
  };

  const loadTrend = async (datasetId?: string) => {
    setBusy(true);
    setError(null);
    try {
      setTrend(await api.evaluationsTrend(datasetId));
    } catch (err) {
      setError(handleError(err));
    } finally {
      setBusy(false);
    }
  };

  return { telemetry, cost, trend, error, busy, loadRun, loadTrend };
}
