import { useI18n } from "../../i18n/useI18n";
import { SourceControl } from "../../layout/SourceControl";
import { RunQueryBar } from "../shared/RunQueryBar";
import styles from "./CommandCenterPage.module.css";
import { CommandCenterGap, CommandCenterPanel } from "./CommandCenterPanel";
import {
  ClaimsSnapshot,
  EventsSnapshot,
  ExperimentsSnapshot,
  RunsSnapshot,
  TelemetrySnapshot,
  UsageSnapshot,
  WorkerTopologySnapshot,
} from "./CommandCenterSnapshots";
import { useCommandCenterQueries } from "./useCommandCenterQueries";

export function CommandCenterPage({
  onExit,
  runId,
  onRunSelected,
}: {
  onExit: () => void;
  runId: string;
  onRunSelected: (id: string) => void;
}) {
  const { language } = useI18n();
  const queries = useCommandCenterQueries(runId);
  return (
    <main className={styles.screen} data-testid="command-center" data-command-center="true">
      <CommandCenterMasthead queries={queries} onExit={onExit} />
      <div className={styles.selection}>
        <RunQueryBar
          runId={runId}
          onSelect={(id) => {
            if (id === runId) queries.refresh();
            else onRunSelected(id);
          }}
        />
        <p className={styles.note}>
          {language === "zh"
            ? "真实查询快照；未读取/失败均不归零。缺少后端能力的面板明确保留缺口，不混入示例指标。"
            : [
                "Actual query snapshots. Missing/failed data never becomes zero; API gaps ",
                "remain explicit rather than mixing in example metrics.",
              ].join("")}
        </p>
      </div>
      <CommandCenterGrid queries={queries} onRunSelected={onRunSelected} />
      <footer className={styles.footer}>
        CANONICAL STATE · USAGE LEDGER · READ ONLY <span>HTTP SNAPSHOT ≠ LIVE TELEMETRY</span>
      </footer>
    </main>
  );
}

function CommandCenterMasthead({
  queries,
  onExit,
}: {
  queries: ReturnType<typeof useCommandCenterQueries>;
  onExit: () => void;
}) {
  const { language } = useI18n();
  const runs = queries.runs.phase === "ready" ? queries.runs.data : null;
  const workers = queries.cluster.phase === "ready" ? queries.cluster.data?.workers : undefined;
  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <div className={styles.mark}>◇</div>
        <div>
          <h1>Research OS</h1>
          <span>COMMAND CENTER · MISSION CONTROL</span>
        </div>
      </div>
      <div className={styles.headerStats}>
        <div>
          <strong>
            {runs === null ? "—" : runs.filter((run) => run.state === "RUNNING").length}
          </strong>
          <small>RUNNING RUNS</small>
        </div>
        <div>
          <strong>{workers?.length ?? "—"}</strong>
          <small>REGISTERED WORKERS</small>
        </div>
      </div>
      <div className={styles.meta}>
        <SourceControl />
        <button type="button" className="btn sm" onClick={queries.refresh}>
          {language === "zh" ? "刷新快照" : "Refresh snapshots"}
        </button>
        <button type="button" className="btn sm" onClick={onExit}>
          ← {language === "zh" ? "返回控制台" : "Back to console"}
        </button>
      </div>
    </header>
  );
}

function CommandCenterGrid({
  queries: q,
  onRunSelected,
}: {
  queries: ReturnType<typeof useCommandCenterQueries>;
  onRunSelected: (id: string) => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  return <CommandCenterPageGrid {...{ zh, q, onRunSelected }} />;
}

interface CommandCenterPageGridProps {
  zh: boolean;
  q: ReturnType<typeof useCommandCenterQueries>;
  onRunSelected: (id: string) => void;
}

function CommandCenterPageGrid({ zh, q, onRunSelected }: CommandCenterPageGridProps) {
  return (
    <div className={styles.grid}>
      <CommandCenterPanel title={zh ? "运行登记" : "REGISTERED RUNS"} state={q.runs}>
        {(runs) => <RunsSnapshot runs={runs} onSelect={onRunSelected} />}
      </CommandCenterPanel>
      <CommandCenterPanel
        title={zh ? "节点拓扑 · 无地理位置" : "WORKER REGISTRY · NO GEOLOCATION"}
        state={q.cluster}
      >
        {(cluster) => <WorkerTopologySnapshot cluster={cluster} />}
      </CommandCenterPanel>
      <CommandCenterPanel title={zh ? "运行遥测" : "RUN TELEMETRY"} state={q.telemetry}>
        {(telemetry) => <TelemetrySnapshot telemetry={telemetry} />}
      </CommandCenterPanel>
      <CommandCenterPanel title={zh ? "论断分布" : "CLAIM DISTRIBUTION"} state={q.claims}>
        {(claims) => <ClaimsSnapshot claims={claims} />}
      </CommandCenterPanel>
      <CommandCenterPanel title={zh ? "使用与费用" : "USAGE AND COST"} state={q.usage}>
        {(usage) => <UsageSnapshot usage={usage} />}
      </CommandCenterPanel>
      <CommandCenterSecondaryPanels {...{ zh, q }} />
    </div>
  );
}

function CommandCenterSecondaryPanels({ zh, q }: Pick<CommandCenterPageGridProps, "zh" | "q">) {
  return (
    <>
      <CommandCenterGap
        title={zh ? "告警信息流" : "ALERTS FEED"}
        reason={
          zh
            ? "告警登记与订阅接口尚未提供，不把审批或失败运行冒充告警。"
            : [
                "No alert registry/subscription API. Approvals and failed runs are not ",
                "substituted as alerts.",
              ].join("")
        }
      />
      <CommandCenterPanel title={zh ? "实验记录" : "EXPERIMENT RECORDS"} state={q.experiments}>
        {(view) => <ExperimentsSnapshot view={view} />}
      </CommandCenterPanel>
      <CommandCenterGap
        title={zh ? "模型活动" : "MODEL ACTIVITY"}
        reason={
          zh
            ? "没有模型活动、延迟或健康时序接口；不把端点启用状态当作实时模型健康。"
            : [
                "No model activity, latency or health time-series API. Endpoint ",
                "enablement is not real-time model health.",
              ].join("")
        }
      />
      <CommandCenterPanel title={zh ? "正式事件" : "PERSISTED EVENTS"} state={q.events}>
        {(events) => <EventsSnapshot events={events} />}
      </CommandCenterPanel>
    </>
  );
}
