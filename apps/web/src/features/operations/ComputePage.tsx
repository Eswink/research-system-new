import { useState, type Dispatch, type SetStateAction } from "react";
import { api } from "../../api/client";
import { MetricCard } from "../../components/charts/MetricCard";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { PageHeader } from "../shared/PageHeader";
import { ClusterPanel } from "./ClusterPanel";
import styles from "./ComputePage.module.css";
import { useCluster, type ClusterState } from "./useCluster";
import { summarizeWorkers } from "./workerPresentation";

export function ComputePage({ runId }: { runId: string }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const cluster = useCluster();
  const [query, setQuery] = useState("");
  return <ComputePagesection {...{ zh, cluster, query, setQuery, runId }} />;
}

interface ComputePagesectionProps {
  zh: boolean;
  cluster: ClusterState;
  query: string;
  setQuery: Dispatch<SetStateAction<string>>;
  runId: string;
}

function ComputePagesection({ zh, cluster, query, setQuery, runId }: ComputePagesectionProps) {
  return (
    <section className={styles.page} data-testid="compute-page">
      <PageHeader
        title={zh ? "计算节点" : "Compute workers"}
        kicker="OPERATIONS / COMPUTE"
        description={
          zh
            ? "Control Plane 注册视图 · 只读，不推断 GPU 利用率或调度容量。"
            : [
                "Control Plane registry · read only. GPU utilization and scheduling ",
                "capacity are not inferred.",
              ].join("")
        }
        actions={
          <button
            className="btn"
            type="button"
            disabled={cluster.busy}
            onClick={() => {
              void cluster.loadCluster();
            }}
          >
            {zh ? "刷新节点" : "Refresh workers"}
          </button>
        }
      />
      <ComputeSummary cluster={cluster} />
      <PanelSection
        title={zh ? "Worker 注册表" : "Worker registry"}
        extra={
          <input
            type="search"
            className={styles.search}
            value={query}
            aria-label={zh ? "搜索节点、状态或平台" : "Search worker, state or platform"}
            placeholder={zh ? "搜索节点、状态或平台…" : "Search worker, state or platform…"}
            onChange={(event) => {
              setQuery(event.target.value);
            }}
          />
        }
      >
        <ClusterPanel cluster={cluster} query={query} />
      </PanelSection>
      <PlacementPanel runId={runId} />
    </section>
  );
}

function ComputeSummary({ cluster }: { cluster: ClusterState }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const summary = summarizeWorkers(cluster.cluster?.workers ?? []);
  const unknown = cluster.cluster === null || cluster.error !== null;
  const metrics = [
    [zh ? "已注册" : "Registered", summary.total],
    [zh ? "就绪 / 执行中" : "Ready / busy", `${String(summary.ready)} / ${String(summary.busy)}`],
    [zh ? "失联 / 已下线" : "Lost / offline", summary.attention],
    [zh ? "配置并发上限" : "Configured concurrency", summary.configuredConcurrency],
  ] as const;
  return (
    <div className={styles.metrics}>
      {metrics.map(([label, value]) => (
        <MetricCard
          key={label}
          label={label}
          value={unknown ? "—" : String(value)}
          sub={zh ? "当前查询投影 · 非实时监控" : "Queried projection · not live monitoring"}
          unknownWarn={unknown}
        />
      ))}
    </div>
  );
}

function PlacementPanel({ runId }: { runId: string }) {
  const { language, t } = useI18n();
  const zh = language === "zh";
  const resource = useResource(runId === "" ? null : runId, () => api.runPlacement(runId));
  return (
    <PanelSection title={zh ? "当前运行的放置结果" : "Selected run placement"}>
      {runId === "" ? (
        <EmptyState message={zh ? "先选择一个运行" : "Select a run first"} />
      ) : resource.phase === "error" ? (
        <ErrorState message={resource.error ?? t("state.error")} />
      ) : resource.data === null ? (
        <LoadingState message={t("state.loading")} />
      ) : (
        <div className={styles.placement}>
          <div className="mono">{resource.data.run_id}</div>
          <p>
            {zh ? "已关联执行任务：" : "Linked execution tasks: "}
            {resource.data.execution_tasks.length}
          </p>
          {resource.data.placements.map((worker) => (
            <div key={worker.worker_ref} className="chip">
              {worker.worker_ref.slice(0, 16)} · {worker.state}
            </div>
          ))}
          {resource.data.placements.length === 0 && (
            <EmptyState
              message={
                zh ? "当前运行没有节点放置记录" : "No recorded worker placement for this run"
              }
            />
          )}
        </div>
      )}
    </PanelSection>
  );
}
