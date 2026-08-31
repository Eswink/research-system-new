import { useCallback, useEffect, useState } from "react";

import { api } from "../../api/client";
import type { ClusterViewDto, RunPlacementDto } from "../../api/types";

export interface ClusterState {
  cluster: ClusterViewDto | null;
  placement: RunPlacementDto | null;
  error: string | null;
  busy: boolean;
  loadCluster: () => Promise<void>;
  loadPlacement: (runId: string) => Promise<void>;
}

/**
 * Worker 集群只读视图（M16）：数据仅来自 Control Plane 只读投影
 * （GET /cluster/workers、GET /runs/{id}/placement）。
 * Console 不直连 Worker，也不拥有调度真相。
 */
export function useCluster(): ClusterState {
  const [cluster, setCluster] = useState<ClusterViewDto | null>(null);
  const [placement, setPlacement] = useState<RunPlacementDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadCluster = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      setCluster(await api.clusterWorkers());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }, []);

  const loadPlacement = useCallback(async (runId: string) => {
    setBusy(true);
    setError(null);
    try {
      setPlacement(await api.runPlacement(runId));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void loadCluster();
  }, [loadCluster]);

  return { cluster, placement, error, busy, loadCluster, loadPlacement };
}
