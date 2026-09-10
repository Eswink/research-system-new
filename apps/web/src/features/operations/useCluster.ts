import { api } from "../../api/client";
import type { ClusterViewDto } from "../../api/types";
import { useResource } from "../../hooks/useResource";

export interface ClusterState {
  cluster: ClusterViewDto | null;
  error: string | null;
  busy: boolean;
  loadCluster: () => void;
}

/**
 * Worker 集群只读视图（M16）：数据仅来自 Control Plane 只读投影
 * （GET /cluster/workers）。Console 不直连 Worker，也不拥有调度真相。
 * 运行放置查询由消费方经 useResource 按键隔离（见 ComputePage）。
 */
export function useCluster(): ClusterState {
  const resource = useResource("cluster", () => api.clusterWorkers());
  return {
    cluster: resource.data,
    error: resource.error,
    busy: resource.phase === "loading",
    loadCluster: () => {
      resource.reload();
    },
  };
}
