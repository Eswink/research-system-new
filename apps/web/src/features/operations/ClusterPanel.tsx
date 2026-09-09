import { useState } from "react";
import type { ClusterWorkerDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { Drawer } from "../../components/Drawer";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import styles from "./ComputePage.module.css";
import type { ClusterState } from "./useCluster";
import { filterWorkers, workerStateLabel, workerTone } from "./workerPresentation";

/** Read-only Control Plane projection. Worker refs remain digests, not raw identities. */
export function ClusterPanel({ cluster, query = "" }: { cluster: ClusterState; query?: string }) {
  const { language, t } = useI18n();
  const [selectedRef, setSelectedRef] = useState<string | null>(null);
  const workers = cluster.cluster?.workers ?? [];
  const selected = workers.find((worker) => worker.worker_ref === selectedRef);
  const zh = language === "zh";
  if (cluster.error !== null) return <ErrorState message={cluster.error} />;
  if (cluster.cluster === null) return <LoadingState message={t("state.loading")} />;
  return (
    <div data-testid="cluster-workers">
      <Table
        columns={workerColumns(zh)}
        rows={filterWorkers(workers, query)}
        rowKey={(worker) => worker.worker_ref}
        selectable
        selectedKey={selectedRef ?? ""}
        onSelectRow={(worker) => {
          setSelectedRef(worker.worker_ref);
        }}
        ariaLabel={zh ? "计算节点" : "Compute workers"}
        empty={
          <EmptyState message={zh ? "没有匹配的已注册节点" : "No matching registered workers"} />
        }
      />
      <Drawer
        open={selected !== undefined}
        onClose={() => {
          setSelectedRef(null);
        }}
        title={zh ? "节点详情 · 只读" : "Worker details · read only"}
      >
        {selected !== undefined && <WorkerDetails worker={selected} />}
      </Drawer>
    </div>
  );
}

function workerColumns(zh: boolean): Column<ClusterWorkerDto>[] {
  return [
    {
      key: "ref",
      header: "Worker",
      sortable: true,
      sortValue: (w) => w.worker_ref,
      render: (w) => (
        <span className="mono" title={w.worker_ref}>
          {w.worker_ref.slice(0, 16)}…
        </span>
      ),
    },
    {
      key: "state",
      header: zh ? "状态" : "State",
      sortable: true,
      sortValue: (w) => w.state,
      render: (w) => (
        <Chip tone={workerTone(w.state)}>
          {workerStateLabel(w.state, zh)}
          {w.drain_requested ? " · DRAIN REQUESTED" : ""}
        </Chip>
      ),
    },
    ...workerDetailColumns(zh),
  ];
}

function workerDetailColumns(zh: boolean): Column<ClusterWorkerDto>[] {
  return [
    { key: "platform", header: zh ? "平台" : "Platform", render: (w) => w.platform },
    { key: "protocol", header: zh ? "协议" : "Protocol", render: (w) => w.protocol_version },
    {
      key: "generation",
      header: zh ? "世代" : "Generation",
      sortable: true,
      sortValue: (w) => w.registration_generation,
      render: (w) => w.registration_generation,
    },
    {
      key: "capacity",
      header: zh ? "配置并发" : "Configured slots",
      sortable: true,
      sortValue: (w) => w.max_concurrency,
      render: (w) => w.max_concurrency,
    },
    {
      key: "heartbeat",
      header: zh ? "最近心跳" : "Last heartbeat",
      render: (w) => w.last_heartbeat ?? "—",
    },
  ];
}

function WorkerDetails({ worker }: { worker: ClusterWorkerDto }) {
  const fields = [
    ["Worker ref", worker.worker_ref],
    ["State", worker.state],
    ["Platform", worker.platform],
    ["Protocol", worker.protocol_version],
    ["Runtime", worker.runtime_version],
    ["Generation", worker.registration_generation],
    ["Configured concurrency", worker.max_concurrency],
    ["Drain requested", String(worker.drain_requested)],
    ["Last heartbeat", worker.last_heartbeat ?? "—"],
  ] as const;
  return (
    <dl className={styles.details}>
      {fields.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
