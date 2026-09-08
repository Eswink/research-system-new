import { api } from "../../api/client";
import { Chip } from "../../components/Chip";
import { MetricCard } from "../../components/charts/MetricCard";
import { ErrorState, LoadingState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { useResource } from "../../hooks/useResource";
import styles from "./CommandCenterPage.module.css";

/**
 * Command Center（T28）：独立大屏，复用已验证的运行/任务/证据/成本/观测查询。
 * 不建立第二套运行状态；缺指标区域保留版式并说明；刷新时间与连接状态分别展示。
 */
export function CommandCenterPage() {
  const { t } = useI18n();
  const runs = useResource("cc-runs", () => api.listRuns());
  const cluster = useResource("cc-cluster", () => api.clusterWorkers());

  if (runs.phase === "loading") {
    return <LoadingState message={t("state.loading")} />;
  }
  if (runs.phase === "error") {
    return <ErrorState message={runs.error ?? t("state.error")} />;
  }
  const runList = runs.data ?? [];
  const workers = cluster.data?.workers ?? [];
  return (
    <div className={styles.screen} data-testid="command-center">
      <header className={styles.header}>
        <div className={styles.title}>{t("page.command-center.command-center")}</div>
        <div className={styles.meta}>
          <Chip tone="accent">{`${t("cc.runs")}: ${String(runList.length)}`}</Chip>
          <span className={styles.stamp}>{t("cc.refreshNote")}</span>
        </div>
      </header>
      <MetricsGrid
        runs={runList}
        workerTotal={workers.length}
        workerOnline={countOnline(workers)}
        clusterUnknown={cluster.data === null}
      />
      <RecentRuns runs={runList} />
      <p className={styles.note}>{t("cc.gapNote")}</p>
    </div>
  );
}

function countOnline(workers: readonly { state: string }[]): number {
  return workers.filter((w) => w.state === "ONLINE" || w.state === "IDLE").length;
}

function MetricsGrid({
  runs,
  workerTotal,
  workerOnline,
  clusterUnknown,
}: {
  runs: readonly { state: string }[];
  workerTotal: number;
  workerOnline: number;
  clusterUnknown: boolean;
}) {
  const { t } = useI18n();
  const count = (s: string) => runs.filter((r) => r.state === s).length;
  return (
    <div className={styles.grid}>
      <MetricCard
        label={t("cc.running")}
        value={String(count("RUNNING"))}
        sub={t("cc.runningSub")}
      />
      <MetricCard
        label={t("cc.succeeded")}
        value={String(count("SUCCEEDED"))}
        sub={t("cc.succeededSub")}
      />
      <MetricCard label={t("cc.failed")} value={String(count("FAILED"))} sub={t("cc.failedSub")} />
      <MetricCard
        label={t("cc.workers")}
        value={`${String(workerOnline)} / ${String(workerTotal)}`}
        sub={t("cc.workersSub")}
        unknownWarn={clusterUnknown}
      />
    </div>
  );
}

interface RunSummary {
  id: string;
  state: string;
  protocol_id: string;
}

function RecentRuns({ runs }: { runs: readonly RunSummary[] }) {
  const { t } = useI18n();
  return (
    <div className={styles.runs}>
      <div className={styles.panelTitle}>{t("cc.recentRuns")}</div>
      {runs.slice(0, 8).map((r) => (
        <a
          key={r.id}
          href={`#/run/timeline?run=${encodeURIComponent(r.id)}`}
          className={styles.runRow}
        >
          <span className="mono">{r.id.slice(0, 20)}</span>
          <Chip tone={stateTone(r.state)}>{r.state}</Chip>
          <span className="mono" style={{ color: "var(--fg-faint)" }}>{r.protocol_id}</span>
        </a>
      ))}
      {runs.length === 0 && <div className={styles.empty}>{t("state.empty")}</div>}
    </div>
  );
}

function stateTone(state: string): "success" | "danger" | "accent" | "neutral" {
  if (state === "SUCCEEDED") {
    return "success";
  }
  if (state === "FAILED") {
    return "danger";
  }
  if (state === "RUNNING") {
    return "accent";
  }
  return "neutral";
}
