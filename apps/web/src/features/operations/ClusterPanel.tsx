import type { ClusterState } from "./useCluster";

const STATE_LABELS: Record<string, string> = {
  REGISTERING: "注册中",
  READY: "就绪",
  BUSY: "执行中",
  DRAINING: "下线中",
  OFFLINE: "已下线",
  LOST: "失联",
};

/**
 * Worker 集群只读面板（M16）：渲染 Control Plane /cluster/workers 投影。
 * 只展示 worker_ref 短 digest（原始 id 不进 UI），不做任何调度决策。
 */
export function ClusterPanel({ cluster }: { cluster: ClusterState }) {
  const workers = cluster.cluster?.workers ?? [];
  if (cluster.error !== null) {
    return <div className="cluster-error">无法读取集群状态：{cluster.error}</div>;
  }
  if (workers.length === 0) {
    return <div className="cluster-empty">当前没有已注册的 Worker。</div>;
  }
  return (
    <table className="cluster-workers" data-testid="cluster-workers">
      <thead>
        <tr>
          <th>Worker</th>
          <th>状态</th>
          <th>协议</th>
          <th>平台</th>
          <th>世代</th>
          <th>并发</th>
          <th>心跳</th>
        </tr>
      </thead>
      <tbody>
        {workers.map((worker) => (
          <tr key={worker.worker_ref}>
            <td title={worker.worker_ref}>{worker.worker_ref.slice(0, 8)}…</td>
            <td>
              {STATE_LABELS[worker.state] ?? worker.state}
              {worker.drain_requested ? "（请求下线）" : ""}
            </td>
            <td>{worker.protocol_version}</td>
            <td>{worker.platform}</td>
            <td>{worker.registration_generation}</td>
            <td>{worker.max_concurrency}</td>
            <td>{worker.last_heartbeat ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
